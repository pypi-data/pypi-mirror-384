import { MapContainer as LMapContainer } from "react-leaflet";
import { useMapEvents } from "react-leaflet/hooks";
import L from "leaflet";
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";
import { refs } from "$/utils/state";

let DefaultIcon = L.icon({
  iconUrl: icon.src ? icon.src : icon,
  shadowUrl: iconShadow.src ? iconShadow.src : iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  tooltipAnchor: [16, -28],
});
L.Marker.prototype.options.icon = DefaultIcon;

export const MapContainer = ({ forwardedRef, ...props }) => (
  <LMapContainer {...props} ref={forwardedRef} />
);

export const MapConsumer = ({ mapRef, eventsHandler }) => {
  if (eventsHandler) {
    const map = useMapEvents(eventsHandler);
    refs[mapRef] = map;
  }
  return null;
};
