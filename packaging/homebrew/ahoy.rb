cask "ahoy" do
  version "0.2.1"

  # Electron-builder names the DMG after productName ("Ahoy Indie Media").
  # x64:   Ahoy Indie Media-{version}.dmg
  # arm64: Ahoy Indie Media-{version}-arm64.dmg
  #
  # To update this cask for a new version:
  #   bash scripts/homebrew-sha256.sh <version>
  # Then commit + push to oooAHOYooo/homebrew-ahoy (Casks/ahoy.rb).

  on_intel do
    url "https://github.com/oooAHOYooo/ahoy-little-platform/releases/download/v#{version}/Ahoy%20Indie%20Media-#{version}.dmg"
    sha256 "REPLACE_WITH_X64_SHA256"
  end

  on_arm do
    url "https://github.com/oooAHOYooo/ahoy-little-platform/releases/download/v#{version}/Ahoy%20Indie%20Media-#{version}-arm64.dmg"
    sha256 "REPLACE_WITH_ARM64_SHA256"
  end

  name "Ahoy"
  desc "Discover and play independent music and shows"
  homepage "https://ahoy.ooo"

  app "Ahoy Indie Media.app"

  zap trash: [
    "~/Library/Application Support/ahoy-indie-media",
    "~/Library/Preferences/com.ahoyindiemedia.desktop.plist",
    "~/Library/Caches/com.ahoyindiemedia.desktop",
    "~/Library/Logs/ahoy-indie-media",
  ]
end
