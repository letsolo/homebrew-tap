cask "lbv" do
  arch arm: "arm64", intel: "amd64"

  version "1.1.3"
  sha256 arm: "cd11c6a8ae57fdebf4a3528acf6cf829a65dabad95620f1325ea6976b3d529fe",
         intel: "a511b7111b341dc765ca779e56df2a666acf1ba40fe890c99b68fb81ad961266"

  url "https://github.com/letsolo/lbv/releases/download/v1.1.3/LoveBridgeVPN-1.1.3-macos-#{arch}.dmg"
  name "LoveBridgeVPN"
  desc "LoveBridgeVPN client"
  homepage "https://github.com/letsolo/lbv"

  depends_on macos: ">= :ventura"

  app "鹊桥VPN.app"
end
