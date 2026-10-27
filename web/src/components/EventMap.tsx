import React, { useEffect, useRef } from 'react';
import { EarthquakeEvent } from '../types';

declare const L: any;

const CARTO_API_KEY = (import.meta.env.VITE_CARTO_API_KEY as string) || 'cb1_4vxo_1_10262ecdf4f01ddd335143ec';

interface EventMapProps {
  events: EarthquakeEvent[];
  selectedEventId?: string | null;
  onSelectEvent?: (event: EarthquakeEvent) => void;
}

export const EventMap: React.FC<EventMapProps> = ({ events, selectedEventId, onSelectEvent }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersLayerRef = useRef<any>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (typeof L === 'undefined') return;

    // Initialize Leaflet map once
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [20, 0],
        zoom: 2,
        minZoom: 1,
        maxZoom: 14,
        zoomControl: true,
      });

      // Dark CARTO basemap with authenticated API key (CARTO expects ?key=...)
      const cartoTileUrl = CARTO_API_KEY
        ? `https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png?key=${encodeURIComponent(CARTO_API_KEY)}&api_key=${encodeURIComponent(CARTO_API_KEY)}`
        : 'https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png';

      const cartoDarkLayer = L.tileLayer(cartoTileUrl, {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions" target="_blank" rel="noopener noreferrer">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
      });

      // Redundant fallback basemap (OpenStreetMap standard, no API key needed)
      const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
        maxZoom: 19
      });

      // Add default dark layer
      cartoDarkLayer.addTo(map);

      // Layer switcher control in top right
      L.control.layers({
        'CARTO Dark Matter': cartoDarkLayer,
        'OpenStreetMap': osmLayer
      }, undefined, { position: 'topright' }).addTo(map);

      markersLayerRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;

    // Clear previous markers
    markersLayer.clearLayers();

    // Color code and size based on magnitude
    const getMagStyle = (mag: number, tsunami: number) => {
      let fillColor = '#eab308'; // yellow (< 3.5)
      let radius = Math.max(mag * 2.8, 4);

      if (mag >= 6.0) {
        fillColor = '#ef4444'; // red (severe)
        radius = Math.max(mag * 4.0, 10);
      } else if (mag >= 4.5) {
        fillColor = '#f97316'; // orange (moderate-strong)
        radius = Math.max(mag * 3.2, 7);
      } else if (mag >= 3.0) {
        fillColor = '#eab308';
      } else {
        fillColor = '#10b981'; // green / minor
      }

      const color = tsunami > 0 ? '#38bdf8' : fillColor;
      return {
        radius,
        fillColor,
        color,
        weight: tsunami > 0 ? 3 : 1.5,
        opacity: 0.9,
        fillOpacity: 0.65
      };
    };

    events.forEach(evt => {
      if (typeof evt.latitude !== 'number' || typeof evt.longitude !== 'number') return;

      const style = getMagStyle(evt.mag, evt.tsunami);
      const isSelected = selectedEventId === evt.event_id;

      if (isSelected) {
        style.weight = 4;
        style.color = '#ffffff';
        style.fillOpacity = 0.9;
      }

      const circle = L.circleMarker([evt.latitude, evt.longitude], style);

      const popupContent = `
        <div style="font-family: inherit; font-size: 12px; color: #0f172a; min-width: 180px;">
          <div style="font-weight: 700; font-size: 14px; margin-bottom: 4px; color: #0284c7;">
            Magnitude ${evt.mag.toFixed(1)} ${evt.mag_type || ''}
          </div>
          <div style="margin-bottom: 4px;"><strong>Location:</strong> ${evt.place}</div>
          <div style="margin-bottom: 4px;"><strong>Depth:</strong> ${evt.depth_km.toFixed(1)} km</div>
          <div style="margin-bottom: 4px;"><strong>Time:</strong> ${new Date(evt.event_time).toUTCString()}</div>
          ${evt.tsunami > 0 ? '<div style="color: #dc2626; font-weight: 700;">⚠ TSUNAMI WARNING FLAGGED</div>' : ''}
          ${evt.url ? `<div style="margin-top: 6px;"><a href="${evt.url}" target="_blank" rel="noopener noreferrer" style="color: #2563eb; text-decoration: underline;">View on USGS &rarr;</a></div>` : ''}
        </div>
      `;

      circle.bindPopup(popupContent);

      circle.on('click', () => {
        if (onSelectEvent) onSelectEvent(evt);
      });

      markersLayer.addLayer(circle);
    });

    // If an event is selected, pan smoothly to it
    if (selectedEventId) {
      const target = events.find(e => e.event_id === selectedEventId);
      if (target) {
        map.setView([target.latitude, target.longitude], 6, { animate: true });
      }
    }
  }, [events, selectedEventId]);

  return (
    <div style={{
      width: '100%',
      height: '420px',
      borderRadius: '10px',
      overflow: 'hidden',
      border: '1px solid #23304c',
      position: 'relative'
    }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />
      <div style={{
        position: 'absolute',
        bottom: '12px',
        right: '12px',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(4px)',
        border: '1px solid #334155',
        borderRadius: '6px',
        padding: '8px 12px',
        fontSize: '11px',
        color: '#94a3b8',
        display: 'flex',
        gap: '12px',
        zIndex: 1000
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }} /> &lt;3.0
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#eab308' }} /> 3.0-4.4
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f97316' }} /> 4.5-5.9
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }} /> 6.0+
        </div>
      </div>
    </div>
  );
};
