import CoreLocation
import MapKit

/// Finds a place by name or address with Apple Maps and works out a walking route to it, as the
/// route message in contracts/MESSAGES.md. Apart from the Tailscale link to the GX10, this is the app's only use of the internet.
/// Apple Maps calls back on the main thread.
final class Places {
    /// Where to look: a square this far across, centred on the user (so 5 km each way).
    static let searchSpan: CLLocationDistance = 10_000

    private var search: MKLocalSearch?
    private var directions: MKDirections?

    /// Looks `query` up near `here` and gives `done` the route message as JSON text. When no place
    /// or no walking route is found the message has an empty polyline, which the GX10 says aloud.
    func route(to query: String, from here: CLLocationCoordinate2D?, done: @escaping (String) -> Void) {
        search?.cancel()
        directions?.cancel()
        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = query
        if let here {
            request.region = MKCoordinateRegion(center: here, latitudinalMeters: Places.searchSpan, longitudinalMeters: Places.searchSpan)
        }
        let search = MKLocalSearch(request: request)
        self.search = search
        search.start { [weak self] response, _ in
            guard let self else { return }
            guard let item = Places.nearest(response?.mapItems ?? [], to: here) else {
                done(Places.message(dest: query, route: nil))
                return
            }
            self.walk(to: item, named: item.name ?? query, done: done)
        }
    }

    private func walk(to item: MKMapItem, named name: String, done: @escaping (String) -> Void) {
        let request = MKDirections.Request()
        request.source = MKMapItem.forCurrentLocation()
        request.destination = item
        request.transportType = .walking
        let directions = MKDirections(request: request)
        self.directions = directions
        directions.calculate { response, _ in
            done(Places.message(dest: name, route: response?.routes.first))
        }
    }

    /// "A coffee shop" means the nearest one, so take the result closest to the user.
    static func nearest(_ items: [MKMapItem], to here: CLLocationCoordinate2D?) -> MKMapItem? {
        guard let here else { return items.first }
        let user = CLLocation(latitude: here.latitude, longitude: here.longitude)
        func distance(_ item: MKMapItem) -> CLLocationDistance {
            let c = item.placemark.coordinate
            return user.distance(from: CLLocation(latitude: c.latitude, longitude: c.longitude))
        }
        return items.min { distance($0) < distance($1) }
    }

    /// The route message. No route gives an empty polyline.
    static func message(dest: String, route: MKRoute?) -> String {
        var m: [String: Any] = ["dest": dest, "polyline": [[Double]](), "steps": [[String: Any]]()]
        if let route {
            m["polyline"] = coordinates(of: route.polyline).map { [$0.latitude, $0.longitude] }
            m["distance_m"] = route.distance.rounded()
            m["eta_min"] = (route.expectedTravelTime / 60).rounded()
            var steps: [[String: Any]] = []
            for step in route.steps where !step.instructions.isEmpty {
                // a step's line starts where its instruction applies
                if let at = coordinates(of: step.polyline).first {
                    steps.append(["lat": at.latitude, "lon": at.longitude, "text": step.instructions])
                }
            }
            m["steps"] = steps
        }
        guard let data = try? JSONSerialization.data(withJSONObject: m),
              let text = String(data: data, encoding: .utf8) else { return "{}" }
        return text
    }

    static func coordinates(of line: MKPolyline) -> [CLLocationCoordinate2D] {
        var out = [CLLocationCoordinate2D](repeating: kCLLocationCoordinate2DInvalid, count: line.pointCount)
        line.getCoordinates(&out, range: NSRange(location: 0, length: line.pointCount))
        return out
    }
}
