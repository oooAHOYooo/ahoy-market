package ooo.ahoy.app;

import android.app.PendingIntent;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.media3.common.AudioAttributes;
import androidx.media3.common.C;
import androidx.media3.common.MediaItem;
import androidx.media3.common.MediaMetadata;
import androidx.media3.common.Player;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.session.MediaLibraryService;
import androidx.media3.session.MediaSession;
import androidx.media3.session.LibraryResult;
import androidx.media3.session.MediaLibraryService.LibraryParams;

import com.google.common.collect.ImmutableList;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Android Auto media library service (Media3).
 *
 * Exposes the Ahoy music catalog as a browsable tree and handles playback via ExoPlayer.
 * Branding color: #ff0060
 */
public class AhoyMediaService extends MediaLibraryService {

    private static final String TAG = "AhoyMediaService";
    private static final String API_BASE = "https://app.ahoy.ooo";

    // Media tree IDs
    private static final String ROOT_ID = "ROOT";
    private static final String MUSIC_ROOT = "MUSIC";
    private static final String RADIO_ROOT = "RADIO";
    private static final String ARTISTS_ROOT = "ARTISTS";
    private static final String PODCASTS_ROOT = "PODCASTS";
    private static final String WHATS_NEW_ROOT = "WHATS_NEW";

    private MediaLibrarySession mediaLibrarySession;
    private ExoPlayer player;

    // Cached data
    private List<JSONObject> tracks = new ArrayList<>();
    private List<JSONObject> artists = new ArrayList<>();
    private List<JSONObject> podcastShows = new ArrayList<>();
    private List<JSONObject> whatsNewItems = new ArrayList<>();
    private JSONObject radioManifest = new JSONObject();
    private List<MediaItem> lastSearchResults = new ArrayList<>();

    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    @Override
    public void onCreate() {
        super.onCreate();

        // Create ExoPlayer
        player = new ExoPlayer.Builder(this)
            .setAudioAttributes(
                new AudioAttributes.Builder()
                    .setContentType(C.AUDIO_CONTENT_TYPE_MUSIC)
                    .setUsage(C.USAGE_MEDIA)
                    .build(),
                true
            )
            .setHandleAudioBecomingNoisy(true)
            .build();

        // Intent to open app
        Intent intent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE);

        // Create MediaLibrarySession
        mediaLibrarySession = new MediaLibrarySession.Builder(this, player, new LibrarySessionCallback())
            .setSessionActivity(pendingIntent)
            .build();

        // Fetch content in background
        executor.execute(this::fetchAllContent);
    }

    @Nullable
    @Override
    public MediaLibrarySession onGetSession(@NonNull MediaSession.ControllerInfo controllerInfo) {
        return mediaLibrarySession;
    }

    @Override
    public void onDestroy() {
        if (player != null) {
            player.release();
            player = null;
        }
        if (mediaLibrarySession != null) {
            mediaLibrarySession.release();
            mediaLibrarySession = null;
        }
        executor.shutdown();
        super.onDestroy();
    }

    private class LibrarySessionCallback implements MediaLibrarySession.Callback {

        @NonNull
        @Override
        public ListenableFuture<LibraryResult<MediaItem>> onGetLibraryRoot(
            @NonNull MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @Nullable LibraryParams params
        ) {
            MediaItem root = new MediaItem.Builder()
                .setMediaId(ROOT_ID)
                .setMediaMetadata(new MediaMetadata.Builder()
                    .setIsBrowsable(true)
                    .setIsPlayable(false)
                    .build())
                .build();
            return Futures.immediateFuture(LibraryResult.ofItem(root, params));
        }

        @NonNull
        @Override
        public ListenableFuture<LibraryResult<ImmutableList<MediaItem>>> onGetChildren(
            @NonNull MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @NonNull String parentId,
            int page,
            int pageSize,
            @Nullable LibraryParams params
        ) {
            List<MediaItem> items = new ArrayList<>();
            switch (parentId) {
                case ROOT_ID:
                    items.add(createBrowsable(RADIO_ROOT, "Radio", "Listen live", null));
                    items.add(createBrowsable(WHATS_NEW_ROOT, "What's New", "Latest updates", null));
                    items.add(createBrowsable(MUSIC_ROOT, "All Music", "Browse all tracks", null));
                    items.add(createBrowsable(ARTISTS_ROOT, "Artists", "Browse by artist", null));
                    items.add(createBrowsable(PODCASTS_ROOT, "Podcasts", "Browse podcasts", null));
                    break;

                case RADIO_ROOT:
                    List<MediaItem> radioQueue = buildRadioQueue();
                    Log.i(TAG, "Radio root requested; queueSize=" + radioQueue.size() + ", currentIndex=" + radioCurrentIndex());
                    items.add(createPlayable("radio:start", "Start Ahoy Radio", radioSubtitle(), null));
                    for (MediaItem radioItem : radioQueue) {
                        items.add(radioItem);
                    }
                    break;

                case WHATS_NEW_ROOT:
                    for (JSONObject item : whatsNewItems) {
                        items.add(mapJsonToMediaItem(item, "whats_new"));
                    }
                    break;

                case MUSIC_ROOT:
                    for (JSONObject track : tracks) {
                        items.add(mapJsonToMediaItem(track, "track"));
                    }
                    break;

                case ARTISTS_ROOT:
                    for (JSONObject artist : artists) {
                        String aid = optString(artist, "id");
                        if (aid.isEmpty()) aid = optString(artist, "slug");
                        items.add(createBrowsable("ARTIST:" + aid, optString(artist, "name"), optString(artist, "type"), optString(artist, "image")));
                    }
                    break;

                case PODCASTS_ROOT:
                    for (JSONObject show : podcastShows) {
                        String id = "PODCAST:" + optString(show, "slug");
                        int epCount = show.optJSONArray("episodes") != null ? show.optJSONArray("episodes").length() : 0;
                        items.add(createBrowsable(id, optString(show, "title"), epCount + " episodes", optString(show, "artwork")));
                    }
                    break;

                default:
                    if (parentId.startsWith("ARTIST:")) {
                        String artistId = parentId.substring(7);
                        String artistName = "";
                        for (JSONObject a : artists) {
                            if (optString(a, "id").equals(artistId) || optString(a, "slug").equals(artistId)) {
                                artistName = optString(a, "name");
                                break;
                            }
                        }
                        for (JSONObject track : tracks) {
                            if (optString(track, "artist").equals(artistName) ||
                                optString(track, "artist_id").equals(artistId) ||
                                optString(track, "artist_slug").equals(artistId)) {
                                items.add(mapJsonToMediaItem(track, "track"));
                            }
                        }
                    } else if (parentId.startsWith("PODCAST:")) {
                        String slug = parentId.substring(8);
                        for (JSONObject show : podcastShows) {
                            if (optString(show, "slug").equals(slug)) {
                                JSONArray episodes = show.optJSONArray("episodes");
                                if (episodes != null) {
                                    for (int i = 0; i < episodes.length(); i++) {
                                        try {
                                            JSONObject ep = episodes.getJSONObject(i);
                                            items.add(mapJsonToMediaItem(ep, "episode"));
                                        } catch (Exception e) {
                                            Log.w(TAG, "Error parsing episode", e);
                                        }
                                    }
                                }
                                break;
                            }
                        }
                    }
                    break;
            }
            return Futures.immediateFuture(LibraryResult.ofItemList(items, params));
        }

        @NonNull
        @Override
        public MediaSession.ConnectionResult onConnect(
            @NonNull MediaSession session,
            @NonNull MediaSession.ControllerInfo controller
        ) {
            // Re-fetch catalog on every Auto reconnect so content stays fresh
            executor.execute(AhoyMediaService.this::fetchAllContent);
            return super.onConnect(session, controller);
        }

        @NonNull
        @Override
        public ListenableFuture<MediaSession.MediaItemsWithStartPosition> onSetMediaItems(
            @NonNull MediaSession mediaSession,
            @NonNull MediaSession.ControllerInfo browser,
            @NonNull List<MediaItem> mediaItems,
            int startIndex,
            long startPositionMs
        ) {
            if (mediaItems.isEmpty()) {
                return Futures.immediateFuture(new MediaSession.MediaItemsWithStartPosition(
                    Collections.emptyList(), 0, androidx.media3.common.C.TIME_UNSET));
            }
            String firstId = mediaItems.get(0).mediaId;

            if (firstId.equals("radio:start") || firstId.startsWith("radio:")) {
                List<MediaItem> radioQueue = buildRadioQueue();
                int radioStart = firstId.equals("radio:start") ? 0 : findQueueIndex(radioQueue, firstId);
                return Futures.immediateFuture(new MediaSession.MediaItemsWithStartPosition(
                    radioQueue, Math.max(0, radioStart), androidx.media3.common.C.TIME_UNSET));
            }
            if (firstId.startsWith("track:")) {
                List<MediaItem> musicQueue = buildMusicQueue();
                int trackStart = findQueueIndex(musicQueue, firstId);
                return Futures.immediateFuture(new MediaSession.MediaItemsWithStartPosition(
                    musicQueue, Math.max(0, trackStart), androidx.media3.common.C.TIME_UNSET));
            }
            if (firstId.startsWith("whats_new:")) {
                List<MediaItem> wnQueue = buildWhatsNewQueue();
                int wnStart = findQueueIndex(wnQueue, firstId);
                return Futures.immediateFuture(new MediaSession.MediaItemsWithStartPosition(
                    wnQueue, Math.max(0, wnStart), androidx.media3.common.C.TIME_UNSET));
            }
            if (firstId.startsWith("episode:")) {
                String episodeId = firstId.substring(8);
                List<MediaItem> epQueue = buildEpisodeQueue(episodeId);
                if (!epQueue.isEmpty()) {
                    int epStart = findQueueIndex(epQueue, firstId);
                    return Futures.immediateFuture(new MediaSession.MediaItemsWithStartPosition(
                        epQueue, Math.max(0, epStart), androidx.media3.common.C.TIME_UNSET));
                }
            }
            return Futures.immediateFuture(new MediaSession.MediaItemsWithStartPosition(
                mediaItems, startIndex, startPositionMs));
        }

        @NonNull
        @Override
        public ListenableFuture<MediaSession.MediaItemsWithStartPosition> onPlaybackResumption(
            @NonNull MediaSession mediaSession,
            @NonNull MediaSession.ControllerInfo controller
        ) {
            List<MediaItem> radioQueue = buildRadioQueue();
            if (!radioQueue.isEmpty()) {
                return Futures.immediateFuture(new MediaSession.MediaItemsWithStartPosition(
                    radioQueue, 0, androidx.media3.common.C.TIME_UNSET));
            }
            List<MediaItem> musicQueue = buildMusicQueue();
            if (!musicQueue.isEmpty()) {
                return Futures.immediateFuture(new MediaSession.MediaItemsWithStartPosition(
                    musicQueue, 0, androidx.media3.common.C.TIME_UNSET));
            }
            return Futures.immediateFuture(new MediaSession.MediaItemsWithStartPosition(
                Collections.emptyList(), 0, androidx.media3.common.C.TIME_UNSET));
        }

        @NonNull
        @Override
        public ListenableFuture<LibraryResult<Void>> onSearch(
            @NonNull MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @NonNull String query,
            @Nullable LibraryParams params
        ) {
            lastSearchResults = buildSearchResults(query);
            session.notifySearchResultChanged(browser, query, lastSearchResults.size(), params);
            return Futures.immediateFuture(LibraryResult.ofVoid());
        }

        @NonNull
        @Override
        public ListenableFuture<LibraryResult<ImmutableList<MediaItem>>> onGetSearchResult(
            @NonNull MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @NonNull String query,
            int page,
            int pageSize,
            @Nullable LibraryParams params
        ) {
            List<MediaItem> results = lastSearchResults.isEmpty()
                ? buildSearchResults(query) : lastSearchResults;
            return Futures.immediateFuture(LibraryResult.ofItemList(ImmutableList.copyOf(results), params));
        }
    }

    private MediaItem createBrowsable(String id, String title, String subtitle, String iconUrl) {
        return new MediaItem.Builder()
            .setMediaId(id)
            .setMediaMetadata(new MediaMetadata.Builder()
                .setTitle(title)
                .setSubtitle(subtitle)
                .setIsBrowsable(true)
                .setIsPlayable(false)
                .setArtworkUri(iconUrl != null ? Uri.parse(iconUrl) : null)
                .build())
            .build();
    }

    private MediaItem createPlayable(String id, String title, String subtitle, String iconUrl) {
        return new MediaItem.Builder()
            .setMediaId(id)
            .setMediaMetadata(new MediaMetadata.Builder()
                .setTitle(title)
                .setSubtitle(subtitle)
                .setIsBrowsable(false)
                .setIsPlayable(true)
                .setArtworkUri(iconUrl != null ? Uri.parse(iconUrl) : null)
                .build())
            .build();
    }

    private MediaItem mapJsonToMediaItem(JSONObject json, String type) {
        String id = type + ":" + optString(json, "id");
        String title = optString(json, "title");
        String artist = optString(json, "artist");
        String artwork = optString(json, "cover_art");
        if (artwork.isEmpty()) artwork = optString(json, "artwork");
        String audioUrl = normalizeAudioUrl(json);

        return new MediaItem.Builder()
            .setMediaId(id)
            .setUri(audioUrl)
            .setMediaMetadata(new MediaMetadata.Builder()
                .setTitle(title)
                .setArtist(artist)
                .setArtworkUri(artwork.isEmpty() ? null : Uri.parse(artwork))
                .setIsBrowsable(false)
                .setIsPlayable(true)
            .build())
            .build();
    }

    private String radioSubtitle() {
        List<JSONObject> items = radioItems();
        if (items.isEmpty()) return "Loading station...";
        int index = Math.min(radioCurrentIndex(), Math.max(0, items.size() - 1));
        JSONObject current = items.get(index);
        String title = optString(current, "title");
        String artist = optString(current, "artist");
        if (artist.isEmpty()) return title.isEmpty() ? "Ahoy Radio" : title;
        return title.isEmpty() ? artist : title + " - " + artist;
    }

    private List<JSONObject> radioItems() {
        List<JSONObject> result = new ArrayList<>();
        JSONArray items = radioManifest.optJSONArray("tracks");
        if (items == null) items = radioManifest.optJSONArray("items");
        if (items != null) {
            for (int i = 0; i < items.length(); i++) {
                result.add(items.optJSONObject(i));
            }
        }
        Log.i(TAG, "radioItems resolved count=" + result.size() + " fallbackTracks=" + tracks.size());
        return result.isEmpty() ? tracks : result;
    }

    private int radioCurrentIndex() {
        if (radioManifest.has("current_index")) return radioManifest.optInt("current_index", 0);
        JSONObject current = radioManifest.optJSONObject("current");
        if (current != null) return current.optInt("current_index", 0);
        return 0;
    }

    private List<MediaItem> buildRadioQueue() {
        List<MediaItem> queue = new ArrayList<>();
        List<JSONObject> items = radioItems();
        if (items.isEmpty()) {
            Log.w(TAG, "buildRadioQueue found no items");
            return queue;
        }

        int startIdx = Math.min(radioCurrentIndex(), Math.max(0, items.size() - 1));
        for (int i = 0; i < items.size(); i++) {
            int idx = (startIdx + i) % items.size();
            JSONObject item = items.get(idx);
            if (item != null) {
                queue.add(mapJsonToMediaItem(item, "radio"));
            }
        }
        Log.i(TAG, "buildRadioQueue built queueSize=" + queue.size() + " startIdx=" + startIdx);
        return queue;
    }

    private List<MediaItem> buildMusicQueue() {
        List<MediaItem> queue = new ArrayList<>();
        for (JSONObject track : tracks) queue.add(mapJsonToMediaItem(track, "track"));
        return queue;
    }

    private List<MediaItem> buildWhatsNewQueue() {
        List<MediaItem> queue = new ArrayList<>();
        for (JSONObject item : whatsNewItems) queue.add(mapJsonToMediaItem(item, "whats_new"));
        return queue;
    }

    private List<MediaItem> buildEpisodeQueue(String episodeId) {
        String targetId = "episode:" + episodeId;
        for (JSONObject show : podcastShows) {
            JSONArray episodes = show.optJSONArray("episodes");
            if (episodes == null) continue;
            List<MediaItem> queue = new ArrayList<>();
            boolean found = false;
            for (int i = 0; i < episodes.length(); i++) {
                try {
                    MediaItem item = mapJsonToMediaItem(episodes.getJSONObject(i), "episode");
                    queue.add(item);
                    if (item.mediaId.equals(targetId)) found = true;
                } catch (Exception e) { /* skip bad episode */ }
            }
            if (found) return queue;
        }
        return Collections.emptyList();
    }

    private int findQueueIndex(List<MediaItem> queue, String targetId) {
        for (int i = 0; i < queue.size(); i++) {
            if (queue.get(i).mediaId.equals(targetId)) return i;
        }
        return 0;
    }

    private List<MediaItem> buildSearchResults(String query) {
        String q = query.toLowerCase().trim();
        List<MediaItem> results = new ArrayList<>();
        for (JSONObject track : tracks) {
            if (optString(track, "title").toLowerCase().contains(q)
                    || optString(track, "artist").toLowerCase().contains(q)) {
                results.add(mapJsonToMediaItem(track, "track"));
            }
        }
        for (JSONObject show : podcastShows) {
            if (optString(show, "title").toLowerCase().contains(q)) {
                JSONArray episodes = show.optJSONArray("episodes");
                if (episodes != null) {
                    for (int i = 0; i < Math.min(episodes.length(), 5); i++) {
                        try { results.add(mapJsonToMediaItem(episodes.getJSONObject(i), "episode")); }
                        catch (Exception e) { /* skip */ }
                    }
                }
            }
        }
        return results;
    }

    private void fetchAllContent() {
        tracks = fetchJsonArray(API_BASE + "/api/music", "tracks");
        artists = fetchJsonArray(API_BASE + "/api/artists", "artists");
        podcastShows = fetchJsonArray(API_BASE + "/api/podcasts", "shows");
        whatsNewItems = fetchJsonArray(API_BASE + "/api/whats-new", "items");
        radioManifest = fetchJsonObject(API_BASE + "/api/radio/live");
        Log.i(TAG, "Loaded content for MediaLibrary tracks=" + tracks.size()
            + " artists=" + artists.size()
            + " podcasts=" + podcastShows.size()
            + " whatsNew=" + whatsNewItems.size()
            + " radioKeys=" + radioManifest.length());
    }

    private JSONObject fetchJsonObject(String urlString) {
        try {
            URL url = new URL(urlString);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("Accept", "application/json");
            conn.setConnectTimeout(15000);
            conn.setReadTimeout(15000);

            BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) sb.append(line);
            reader.close();
            conn.disconnect();

            return new JSONObject(sb.toString());
        } catch (Exception e) {
            Log.w(TAG, "Failed to fetch JSON object from " + urlString, e);
            return new JSONObject();
        }
    }

    private List<JSONObject> fetchJsonArray(String urlString, String key) {
        List<JSONObject> result = new ArrayList<>();
        try {
            URL url = new URL(urlString);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("Accept", "application/json");
            conn.setConnectTimeout(10000);
            conn.setReadTimeout(10000);

            if (conn.getResponseCode() == 200) {
                BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) sb.append(line);
                reader.close();

                JSONObject json = new JSONObject(sb.toString());
                JSONArray array = json.optJSONArray(key);
                if (array != null) {
                    for (int i = 0; i < array.length(); i++) {
                        result.add(array.getJSONObject(i));
                    }
                }
            }
            conn.disconnect();
        } catch (Exception e) {
            Log.e(TAG, "Error fetching " + urlString, e);
        }
        return result;
    }

    private static String optString(JSONObject obj, String key) {
        return obj.optString(key, "");
    }

    private String normalizeAudioUrl(JSONObject item) {
        String audioUrl = optString(item, "audio_url");
        if (audioUrl.isEmpty()) audioUrl = optString(item, "url");
        if (audioUrl.isEmpty()) audioUrl = optString(item, "preview_url");
        return normalizeAudioUrl(audioUrl);
    }

    private String normalizeAudioUrl(String rawUrl) {
        if (rawUrl == null) return "";
        String resolved = rawUrl.trim();
        if (resolved.isEmpty()) return "";
        if (resolved.startsWith("/")) {
            resolved = API_BASE + resolved;
        }
        try {
            return new URI(resolved).toASCIIString();
        } catch (URISyntaxException e) {
            return resolved.replace(" ", "%20");
        }
    }
}
