import { useEffect, useCallback } from "react";
import useStore from "../store/useStore";

export default function useUserLocation(enabled = true) {
  const location = useStore((s) => s.location);
  const setLocation = useStore((s) => s.setLocation);
  const setError = useStore((s) => s.setError);
  const setLoading = useStore((s) => s.setLoading);

  // 🔥 NEW
  const attempted = useStore((s) => s.locationAttempted);
  const setAttempted = useStore((s) => s.setLocationAttempted);

  // =========================
  // FETCH LOCATION
  // =========================
  const fetchLocation = useCallback(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    if (!navigator.geolocation) {
      setError("Geolocation not supported on this device");
      setAttempted(true);
      return;
    }

    setLoading(true);

    const options = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000,
    };

    let isMounted = true;

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (!isMounted) return;

        setLocation({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
        });

        setLoading(false);
        setAttempted(true);
      },
      (err) => {
        if (!isMounted) return;

        let message = "Unable to fetch location";

        if (err.code === 1) message = "Location permission denied";
        if (err.code === 2) message = "Location unavailable";
        if (err.code === 3) message = "Location request timed out";

        setError(message);
        setLoading(false);
        setAttempted(true);

        console.warn("Location error:", err.message);
      },
      options
    );

    return () => {
      isMounted = false;
    };
  }, [enabled, setLocation, setError, setLoading, setAttempted]);

  // =========================
  // AUTO FETCH
  // =========================
  useEffect(() => {
    if (!enabled) return;

    if (!location && !attempted) {
      fetchLocation();
    }
  }, [enabled, location, attempted, fetchLocation]);

  return {
    location,
    fetchLocation, // manual retry still works
  };
}