cask "lbv" do
  arch arm: "arm64", intel: "amd64"

  version "1.1.2"
  sha256 arm: "47437f882458703636868d395bf2a39ba53db5c5c5fba05f425df56b9dfbb668",
         intel: "30c081c51879353df6603ed6859bed8a7de48e05bb2314791ffaca3ffb1744dd"

  url "https://github.com/letsolo/lbv/releases/download/v1.1.2/LoveBridgeVPN-1.1.2-macos-#{arch}.dmg"
  name "LoveBridgeVPN"
  desc "LoveBridgeVPN client"
  homepage "https://github.com/letsolo/lbv"

  depends_on macos: ">= :ventura"

  app "鹊桥VPN.app"
end
