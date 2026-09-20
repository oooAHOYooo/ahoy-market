import CarPlay
import MediaPlayer
import AVFoundation

/**
 * CarPlay scene delegate for Ahoy Indie Media.
 *
 * Displays a tab bar with:
 *   - Radio (live station — tunes in at the current sync position)
 *   - What's New (editorial feed)
 *   - Music (list of all tracks)
 *   - Artists (list of artists → their tracks)
 *   - Podcasts (list of shows → episodes)
 *   - Search
 *
 * NOTE: CarPlay requires an Apple-approved entitlement.
 * Apply at: https://developer.apple.com/contact/carplay/
 * Select "Audio" app type → you'll receive a CarPlay entitlement provisioning profile.
 *
 * Until the entitlement is approved, this code compiles but CarPlay won't launch the app.
 */
@available(iOS 14.0, *)
class AhoyCarPlaySceneDelegate: UIResponder, CPTemplateApplicationSceneDelegate {

    var interfaceController: CPInterfaceController?
    private let apiBase = "https://app.ahoy.ooo"

    // Cached data
    private var tracks: [[String: Any]] = []
    private var artists: [[String: Any]] = []
    private var podcastShows: [[String: Any]] = []
    private var whatsNewItems: [[String: Any]] = []
    private var radioManifest: [String: Any] = [:]
    private var radioQueuePlayer: AVQueuePlayer?
    private var radioItemObservers: [NSObjectProtocol] = []
    private var radioOrderedItems: [[String: Any]] = []

    // MARK: - Scene lifecycle

    func templateApplicationScene(
        _ templateApplicationScene: CPTemplateApplicationScene,
        didConnect interfaceController: CPInterfaceController
    ) {
        self.interfaceController = interfaceController
        fetchAllContent { [weak self] in
            guard let self = self else { return }
            let tabBar = self.buildTabBar()
            interfaceController.setRootTemplate(tabBar, animated: true, completion: nil)
        }
    }

    func templateApplicationScene(
        _ templateApplicationScene: CPTemplateApplicationScene,
        didDisconnectInterfaceController interfaceController: CPInterfaceController
    ) {
        self.interfaceController = nil
        cleanupRadioObservers()
        radioQueuePlayer = nil
    }

    // MARK: - Tab bar

    private func buildTabBar() -> CPTabBarTemplate {
        let tabBar = CPTabBarTemplate(templates: [
            buildRadioTab(),
            buildWhatsNewTab(),
            buildMusicTab(),
            buildArtistsTab(),
            buildPodcastsTab(),
            buildSearchTab(),
        ])
        return tabBar
    }

    // MARK: - Radio tab

    private func buildRadioTab() -> CPListTemplate {
        let item = CPListItem(text: "Ahoy Radio", detailText: radioSubtitle())
        item.setImage(UIImage(systemName: "radio.fill"))
        item.handler = { [weak self] _, completion in
            self?.playRadio()
            completion()
        }
        let template = CPListTemplate(title: "Radio", sections: [CPListSection(items: [item])])
        template.tabImage = UIImage(systemName: "radio.fill")
        return template
    }

    private func playRadio() {
        let items = radioItems()
        guard !items.isEmpty else { return }
        playRadioQueue(items: items, startIndex: radioCurrentIndex())
    }

    // MARK: - What's New tab

    private func buildWhatsNewTab() -> CPListTemplate {
        let listItems: [CPListItem] = whatsNewItems.prefix(20).map { item in
            let title = item["title"] as? String ?? "Update"
            let date = item["date"] as? String ?? ""
            let row = CPListItem(text: title, detailText: date)
            row.setImage(UIImage(systemName: "sparkles"))
            return row
        }
        let section = listItems.isEmpty
            ? CPListSection(items: [CPListItem(text: "No updates yet", detailText: nil)])
            : CPListSection(items: listItems)
        let template = CPListTemplate(title: "What's New", sections: [section])
        template.tabImage = UIImage(systemName: "sparkles")
        return template
    }

    // MARK: - Music tab

    private func buildMusicTab() -> CPListTemplate {
        let items = tracks.prefix(100).map { track -> CPListItem in
            let title = track["title"] as? String ?? "Unknown"
            let artist = track["artist"] as? String ?? ""
            let item = CPListItem(text: title, detailText: artist)
            item.handler = { [weak self] _, completion in
                self?.playTrack(track)
                completion()
            }
            return item
        }
        let template = CPListTemplate(title: "Music", sections: [CPListSection(items: items)])
        template.tabImage = UIImage(systemName: "music.note.list")
        return template
    }

    // MARK: - Artists tab

    private func buildArtistsTab() -> CPListTemplate {
        let items = artists.map { artist -> CPListItem in
            let name = artist["name"] as? String ?? "Unknown"
            let type = artist["type"] as? String ?? "Artist"
            let item = CPListItem(text: name, detailText: type)
            item.handler = { [weak self] _, completion in
                self?.showArtistTracks(artist)
                completion()
            }
            return item
        }
        let template = CPListTemplate(title: "Artists", sections: [CPListSection(items: items)])
        template.tabImage = UIImage(systemName: "person.3.fill")
        return template
    }

    private func showArtistTracks(_ artist: [String: Any]) {
        let artistName = artist["name"] as? String ?? ""
        let artistId = "\(artist["id"] ?? "")"
        let artistTracks = tracks.filter { track in
            let trackArtist = track["artist"] as? String ?? ""
            let trackArtistId = "\(track["artist_id"] ?? "")"
            return trackArtist == artistName || trackArtistId == artistId
        }
        let items = artistTracks.map { track -> CPListItem in
            let title = track["title"] as? String ?? "Unknown"
            let item = CPListItem(text: title, detailText: artistName)
            item.handler = { [weak self] _, completion in
                self?.playTrack(track)
                completion()
            }
            return item
        }
        let template = CPListTemplate(title: artistName, sections: [CPListSection(items: items)])
        interfaceController?.pushTemplate(template, animated: true, completion: nil)
    }

    // MARK: - Podcasts tab

    private func buildPodcastsTab() -> CPListTemplate {
        let items = podcastShows.map { show -> CPListItem in
            let title = show["title"] as? String ?? "Unknown"
            let episodes = show["episodes"] as? [[String: Any]] ?? []
            let item = CPListItem(text: title, detailText: "\(episodes.count) episodes")
            item.handler = { [weak self] _, completion in
                self?.showPodcastEpisodes(show)
                completion()
            }
            return item
        }
        let template = CPListTemplate(title: "Podcasts", sections: [CPListSection(items: items)])
        template.tabImage = UIImage(systemName: "mic.fill")
        return template
    }

    private func showPodcastEpisodes(_ show: [String: Any]) {
        let showTitle = show["title"] as? String ?? "Podcast"
        let episodes = show["episodes"] as? [[String: Any]] ?? []
        let items = episodes.map { ep -> CPListItem in
            let title = ep["title"] as? String ?? "Episode"
            let date = ep["date"] as? String ?? ""
            let item = CPListItem(text: title, detailText: date)
            item.handler = { [weak self] _, completion in
                self?.playEpisode(ep, showTitle: showTitle, artwork: show["artwork"] as? String)
                completion()
            }
            return item
        }
        let template = CPListTemplate(title: showTitle, sections: [CPListSection(items: items)])
        interfaceController?.pushTemplate(template, animated: true, completion: nil)
    }

    // MARK: - Search tab

    private func buildSearchTab() -> CPSearchTemplate {
        let search = CPSearchTemplate()
        search.delegate = self
        search.tabImage = UIImage(systemName: "magnifyingglass")
        return search
    }

    // MARK: - Playback helpers

    private func playTrack(_ track: [String: Any]) {
        let audioUrl = track["audio_url"] as? String ?? track["url"] as? String ?? ""
        let title = track["title"] as? String ?? "Unknown"
        let artist = track["artist"] as? String ?? ""
        let artUrl = track["cover_art"] as? String ?? ""
        playAudio(url: audioUrl, title: title, artist: artist, artworkUrl: artUrl)
    }

    private func playEpisode(_ episode: [String: Any], showTitle: String, artwork: String?) {
        let audioUrl = episode["audio_url"] as? String ?? episode["url"] as? String ?? ""
        let title = episode["title"] as? String ?? "Episode"
        playAudio(url: audioUrl, title: title, artist: showTitle, artworkUrl: artwork ?? "")
    }

    private func radioItems() -> [[String: Any]] {
        if let items = radioManifest["tracks"] as? [[String: Any]], !items.isEmpty {
            return items
        }
        return tracks
    }

    private func radioCurrentIndex() -> Int {
        if let index = radioManifest["current_index"] as? Int {
            return max(0, index)
        }
        if let current = radioManifest["current"] as? [String: Any],
           let index = current["current_index"] as? Int {
            return max(0, index)
        }
        return 0
    }

    private func radioSubtitle() -> String {
        let items = radioItems()
        guard !items.isEmpty else { return "Loading station..." }
        let index = min(radioCurrentIndex(), max(0, items.count - 1))
        let current = items[index]
        let title = current["title"] as? String ?? "Now playing"
        let artist = current["artist"] as? String ?? ""
        return artist.isEmpty ? title : "\(title) — \(artist)"
    }

    private func cleanupRadioObservers() {
        for observer in radioItemObservers {
            NotificationCenter.default.removeObserver(observer)
        }
        radioItemObservers.removeAll()
    }

    private func normalizedAudioURL(_ raw: String?) -> URL? {
        guard var resolved = raw?.trimmingCharacters(in: .whitespacesAndNewlines),
              !resolved.isEmpty else { return nil }
        if resolved.hasPrefix("/") { resolved = apiBase + resolved }
        if let url = URL(string: resolved) { return url }
        return URL(string: resolved.replacingOccurrences(of: " ", with: "%20"))
    }

    private func configureBuffering(_ item: AVPlayerItem) {
        item.preferredForwardBufferDuration = 30
        item.canUseNetworkResourcesForLiveStreamingWhilePaused = true
    }

    private func handleRadioPlaybackFailure() {
        guard let player = radioQueuePlayer else { return }
        player.advanceToNextItem()
        player.play()
    }

    // MARK: - Radio queue playback

    private func playRadioQueue(items: [[String: Any]], startIndex: Int) {
        guard !items.isEmpty else { return }

        cleanupRadioObservers()
        let safeStart = min(max(0, startIndex), items.count - 1)
        let ordered = Array(items[safeStart...]) + Array(items[..<safeStart])
        radioOrderedItems = ordered

        let queueItems: [(item: [String: Any], playerItem: AVPlayerItem)] = ordered.compactMap { item in
            let audioUrl = item["audio_url"] as? String ?? item["url"] as? String ?? item["preview_url"] as? String ?? ""
            guard let url = normalizedAudioURL(audioUrl) else { return nil }
            let playerItem = AVPlayerItem(url: url)
            configureBuffering(playerItem)
            return (item, playerItem)
        }
        guard !queueItems.isEmpty else { return }

        let player = AVQueuePlayer(items: queueItems.map { $0.playerItem })
        player.automaticallyWaitsToMinimizeStalling = true
        radioQueuePlayer = player
        AhoyAudioPlayer.shared.player = player

        // Failure / stall observers — skip bad items
        for pair in queueItems {
            for name in [AVPlayerItem.failedToPlayToEndTimeNotification, AVPlayerItem.playbackStalledNotification] {
                let obs = NotificationCenter.default.addObserver(
                    forName: name, object: pair.playerItem, queue: .main
                ) { [weak self] _ in self?.handleRadioPlaybackFailure() }
                radioItemObservers.append(obs)
            }
        }

        // Now Playing updates — fire when each track finishes so the next track's
        // metadata reaches the lock screen / Bluetooth head unit / CarPlay display.
        for (idx, pair) in queueItems.enumerated() {
            let nextIdx = idx + 1
            let obs = NotificationCenter.default.addObserver(
                forName: AVPlayerItem.didPlayToEndTimeNotification,
                object: pair.playerItem,
                queue: .main
            ) { [weak self] _ in
                guard let self = self, nextIdx < self.radioOrderedItems.count else { return }
                let next = self.radioOrderedItems[nextIdx]
                self.updateNowPlaying(
                    title: next["title"] as? String ?? "Ahoy Radio",
                    artist: next["artist"] as? String ?? "Live station",
                    artworkUrl: next["cover_art"] as? String ?? ""
                )
            }
            radioItemObservers.append(obs)
        }

        player.play()

        // Initial Now Playing + remote commands for steering wheel / head unit
        let first = queueItems.first?.item ?? [:]
        updateNowPlaying(
            title: first["title"] as? String ?? "Ahoy Radio",
            artist: first["artist"] as? String ?? "Live station",
            artworkUrl: first["cover_art"] as? String ?? ""
        )
        configureRemoteCommandCenter(for: player)

        // Surface the Now Playing template on the CarPlay screen
        if let controller = interfaceController {
            controller.pushTemplate(CPNowPlayingTemplate.shared, animated: true, completion: nil)
        }
    }

    // MARK: - Single-track playback

    private func playAudio(url: String, title: String, artist: String, artworkUrl: String) {
        guard let audioURL = normalizedAudioURL(url) else { return }
        cleanupRadioObservers()
        radioQueuePlayer = nil
        let playerItem = AVPlayerItem(url: audioURL)
        configureBuffering(playerItem)
        let player = AVPlayer(playerItem: playerItem)
        AhoyAudioPlayer.shared.player = player
        player.play()
        updateNowPlaying(title: title, artist: artist, artworkUrl: artworkUrl)
        configureRemoteCommandCenter(for: player)
        if let controller = interfaceController {
            controller.pushTemplate(CPNowPlayingTemplate.shared, animated: true, completion: nil)
        }
    }

    // MARK: - Now Playing + Remote Commands

    private func updateNowPlaying(title: String, artist: String, artworkUrl: String) {
        var info: [String: Any] = [
            MPMediaItemPropertyTitle: title,
            MPMediaItemPropertyArtist: artist,
            MPNowPlayingInfoPropertyPlaybackRate: 1.0,
        ]
        if !artworkUrl.isEmpty, let artURL = URL(string: artworkUrl) {
            URLSession.shared.dataTask(with: artURL) { data, _, _ in
                if let data = data, let image = UIImage(data: data) {
                    let artwork = MPMediaItemArtwork(boundsSize: image.size) { _ in image }
                    var updated = MPNowPlayingInfoCenter.default().nowPlayingInfo ?? info
                    updated[MPMediaItemPropertyArtwork] = artwork
                    DispatchQueue.main.async {
                        MPNowPlayingInfoCenter.default().nowPlayingInfo = updated
                    }
                }
            }.resume()
        }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }

    private func configureRemoteCommandCenter(for player: AVPlayer) {
        let cc = MPRemoteCommandCenter.shared()
        cc.playCommand.isEnabled = true
        cc.pauseCommand.isEnabled = true
        cc.stopCommand.isEnabled = true
        cc.nextTrackCommand.isEnabled = false
        cc.previousTrackCommand.isEnabled = false
        cc.changePlaybackPositionCommand.isEnabled = false

        cc.playCommand.removeTarget(nil)
        cc.pauseCommand.removeTarget(nil)
        cc.stopCommand.removeTarget(nil)

        cc.playCommand.addTarget { _ in player.play(); return .success }
        cc.pauseCommand.addTarget { _ in player.pause(); return .success }
        cc.stopCommand.addTarget { _ in player.pause(); return .success }
    }

    // MARK: - Network

    private func fetchAllContent(completion: @escaping () -> Void) {
        let group = DispatchGroup()

        group.enter()
        fetchJSON(path: "/api/music", key: "tracks") { [weak self] items in
            self?.tracks = items; group.leave()
        }
        group.enter()
        fetchJSON(path: "/api/artists", key: "artists") { [weak self] items in
            self?.artists = items; group.leave()
        }
        group.enter()
        fetchJSON(path: "/api/podcasts", key: "shows") { [weak self] items in
            self?.podcastShows = items; group.leave()
        }
        group.enter()
        fetchJSON(path: "/api/whats-new", key: "items") { [weak self] items in
            self?.whatsNewItems = items; group.leave()
        }
        group.enter()
        fetchJSONObject(path: "/api/radio/live") { [weak self] json in
            self?.radioManifest = json; group.leave()
        }

        group.notify(queue: .main) { completion() }
    }

    private func fetchJSONObject(path: String, completion: @escaping ([String: Any]) -> Void) {
        guard let url = URL(string: apiBase + path) else { completion([:]); return }
        var request = URLRequest(url: url)
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 15
        URLSession.shared.dataTask(with: request) { data, _, error in
            guard let data = data, error == nil,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                DispatchQueue.main.async { completion([:]) }
                return
            }
            DispatchQueue.main.async { completion(json) }
        }.resume()
    }

    private func fetchJSON(path: String, key: String, completion: @escaping ([[String: Any]]) -> Void) {
        guard let url = URL(string: apiBase + path) else { completion([]); return }
        var request = URLRequest(url: url)
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 15
        URLSession.shared.dataTask(with: request) { data, _, error in
            guard let data = data, error == nil,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let items = json[key] as? [[String: Any]] else {
                DispatchQueue.main.async { completion([]) }
                return
            }
            DispatchQueue.main.async { completion(items) }
        }.resume()
    }
}

// MARK: - Search delegate

extension AhoyCarPlaySceneDelegate: CPSearchTemplateDelegate {
    func searchTemplate(
        _ searchTemplate: CPSearchTemplate,
        updatedSearchText searchText: String,
        completionHandler: @escaping ([CPListItem]) -> Void
    ) {
        let encoded = searchText.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        fetchJSON(path: "/api/search?q=\(encoded)", key: "results") { results in
            let items = results.map { res -> CPListItem in
                let title = res["title"] as? String ?? "Unknown"
                let artist = res["artist"] as? String ?? ""
                let item = CPListItem(text: title, detailText: artist)
                item.handler = { [weak self] _, completion in
                    self?.playTrack(res)
                    completion()
                }
                return item
            }
            completionHandler(items)
        }
    }
}

// MARK: - Shared audio player

/// Singleton so AVPlayer/AVQueuePlayer instance persists across CarPlay template transitions.
class AhoyAudioPlayer {
    static let shared = AhoyAudioPlayer()
    var player: AVPlayer?
    private init() {}
}
