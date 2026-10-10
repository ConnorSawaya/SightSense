import CoreLocation

/// GPS position and compass heading for the frame header. Values are nil until known.
final class Location: NSObject, CLLocationManagerDelegate {
    var onUpdate: ((FrameEncoder.Extras) -> Void)?

    private let manager = CLLocationManager()
    private var extras = FrameEncoder.Extras()

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.headingFilter = 1
        manager.headingOrientation = .portrait  // the phone is mounted upright on the cane
    }

    func start() {
        manager.requestWhenInUseAuthorization()
        manager.startUpdatingLocation()
        if CLLocationManager.headingAvailable() { manager.startUpdatingHeading() }
    }

    func stop() {
        manager.stopUpdatingLocation()
        manager.stopUpdatingHeading()
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let l = locations.last, l.horizontalAccuracy >= 0 else { return }
        extras.lat = l.coordinate.latitude
        extras.lon = l.coordinate.longitude
        extras.gpsAccuracy = l.horizontalAccuracy
        onUpdate?(extras)
    }

    func locationManager(_ manager: CLLocationManager, didUpdateHeading h: CLHeading) {
        guard h.headingAccuracy >= 0 else { return }
        extras.heading = h.trueHeading >= 0 ? h.trueHeading : h.magneticHeading
        onUpdate?(extras)
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        // Keep sending frames; the GX10 treats missing position as unavailable.
    }
}
