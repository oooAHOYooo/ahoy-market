import UIKit
import Capacitor

final class PortraitBridgeViewController: CAPBridgeViewController {
    override var shouldAutorotate: Bool {
        return true
    }

    override var supportedInterfaceOrientations: UIInterfaceOrientationMask {
        return .allButUpsideDown
    }
}
