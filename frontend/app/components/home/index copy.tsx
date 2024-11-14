import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';
import { LngLatBoundsLike } from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Layer, Map, MapRef, Source, useControl } from 'react-map-gl';
import { MapboxOverlay } from '@deck.gl/mapbox/dist/es5/index.js';
import { PathLayer } from '@deck.gl/layers/dist/es5/index.js';
import { Box, Fade } from '@chakra-ui/react';
import { Feature, FeatureCollection, Point } from 'geojson';
import { interpolateInferno, scaleSequential } from 'd3';

import { Run } from './types';
import { RunDetails } from './run-details';
import { useMapImage } from './use-map-image-hook';
import runs from '~/runs.json';
import compassUrl from './compass.png';

import { useFetch } from '$utils/use-fetch-hook';
import { usePreviousValue } from '$utils/use-effect-previous';

const PT_BOUNDS: LngLatBoundsLike = [
  [-11.8, 35.7],
  [-4.2, 43.6]
];

export const COLOR_WARM = ['#ff7b00', '#ff9533', '#ffb066', '#ffca99'];
export const COLOR_COLD = ['#0ac8e5', '#3bd3ea', '#6cdeef', '#9de9f5'];

function DeckGLOverlay(props) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

export function Component() {
  const mapRef = useRef<MapRef>(null);
  const [cursor, setCursor] = useState<string>('auto');
  const [selectedRun, setSelectedRun] = useState(null);
  const [selectedSegmentType, setSegmentType] = useState('fastest');

  const [viewState, setViewState] = useState({
    longitude: -10,
    latitude: 40,
    zoom: 6,
    pitch: 0
  });

  useMapImage({
    mapRef,
    url: compassUrl,
    name: 'compass'
  });

  const mouseMoveHandler = useCallback((e) => {
    mapRef.current?.removeFeatureState({
      source: 'runs-all'
    });

    if (e.features.length > 0) {
      mapRef.current?.setFeatureState(
        { source: 'runs-all', id: e.features[0].id },
        { hover: true }
      );
    }
  }, []);

  const onMouseEnter = useCallback(() => setCursor('pointer'), []);
  const onMouseLeave = useCallback(() => setCursor('auto'), []);
  const onMouseClick = useCallback((e) => {
    setSelectedRun(e.features[0].id);
  }, []);

  const { status, error, data } = useFetch<Run>(
    selectedRun ? `/runs/run-${selectedRun}.json` : undefined
  );

  const previousData = usePreviousValue(data);

  useEffect(() => {
    const mapInstance = mapRef.current;
    if (!mapInstance) return;

    if (!previousData && data) {
      mapInstance.fitBounds(data.bbox, {
        padding: { right: 150, top: 48, bottom: 48, left: 48 }
      });
      mapInstance.once('moveend', () => {
        mapInstance.flyTo({
          pitch: 30
        });
      });
    }

    if (previousData && !data) {
      mapInstance.flyTo({
        pitch: 0,
        bearing: 0
      });
    }
  }, [previousData, data]);

  const kmMarks = useMemo<FeatureCollection | undefined>(() => {
    if (!data) {
      return undefined;
    }

    const features = data.splits.reduce<Feature<Point>[]>((acc, split, idx) => {
      let points = acc;
      if (!idx) {
        points = points.concat({
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: split.geometry.coordinates[0]
          },
          properties: {
            label: 'S'
          }
        });
      }

      points = points.concat({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates:
            split.geometry.coordinates[split.geometry.coordinates.length - 1]
        },
        properties: {
          label: idx === data.splits.length - 1 ? 'F' : `${idx + 1}`
        }
      });

      return points;
    }, []);

    return {
      type: 'FeatureCollection',
      features
    };
  }, [data]);

  const segmentData = useMemo(() => {
    if (!data) return undefined;

    return [...data.segments]
      .reverse()
      .filter((d) => d.type === selectedSegmentType)
      .map((data, idx) => {
        const coords = data.geojson.geometry.coordinates;
        const colors = data.type === 'fastest' ? COLOR_WARM : COLOR_COLD;

        return {
          path: coords.map(([lng, lat]) => [lng, lat, 100 * (idx + 1)]),
          color: [...colors].reverse()[idx % 3]
        };
      });
  }, [data, selectedSegmentType]);

  const segmentsPathLayer = useMemo(() => {
    if (!segmentData) return undefined;

    return new PathLayer({
      id: 'slow-fast-runs',
      data: segmentData,
      widthMinPixels: 2,
      widthScale: 5,
      getPath: (d) => d.path,
      getColor: (d) => {
        const hex = d.color;
        // convert to RGB
        return hex.match(/[0-9a-f]{2}/g).map((x) => parseInt(x, 16));
      },
      getWidth: 2,
      jointRounded: true,
      capRounded: true
    });
  }, [segmentData]);

  return (
    <Box position='absolute' inset={0}>
      <Map
        ref={mapRef}
        {...viewState}
        maxBounds={PT_BOUNDS}
        mapboxAccessToken={process.env.MAPBOX_TOKEN!}
        onMove={(evt) => setViewState(evt.viewState)}
        mapStyle='mapbox://styles/devseed/clsw0e8w400gt01qu3fgafgc7'
        interactiveLayerIds={['runs']}
        cursor={cursor}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
        onMouseMove={mouseMoveHandler}
        onClick={onMouseClick}
      >
        {!!segmentsPathLayer && <DeckGLOverlay layers={[segmentsPathLayer]} />}

        {!data && (
          <Source
            type='raster'
            id='runs-heat'
            tiles={['/run-heatmap/{z}/{x}/{y}.png']}
          >
            <Layer
              type='raster'
              id='runs-heat'
              paint={{
                'raster-opacity': [
                  'interpolate',
                  ['exponential', 0.5],
                  ['zoom'],
                  16,
                  1,
                  18,
                  0
                ]
              }}
            />
          </Source>
        )}
        <Source type='geojson' id='runs-all' data={runs} promoteId='id'>
          {!data && (
            <Layer
              type='line'
              id='runs'
              layout={{
                'line-join': 'round',
                'line-cap': 'round'
              }}
              paint={{
                'line-color': [
                  'interpolate',
                  ['exponential', 0.5],
                  ['zoom'],
                  15.5,
                  '#627BC1',
                  16,
                  [
                    'case',
                    ['boolean', ['feature-state', 'hover'], false],
                    '#627BC1',
                    '#ff8c00'
                  ]
                ],
                'line-width': 6,
                'line-opacity': [
                  'interpolate',
                  ['exponential', 0.5],
                  ['zoom'],
                  15.5,
                  [
                    'case',
                    ['boolean', ['feature-state', 'hover'], false],
                    1,
                    0
                  ],
                  16,
                  1
                ]
              }}
            />
          )}
          {data && (
            <Layer
              id='run-single'
              type='line'
              layout={{
                'line-join': 'round',
                'line-cap': 'round'
              }}
              paint={{
                'line-color': '#ffffff',
                'line-width': 3
              }}
              filter={['==', 'id', selectedRun]}
            />
          )}
          {data && (
            <Layer
              id='run-single-dir'
              type='symbol'
              minzoom={13}
              filter={['==', 'id', selectedRun]}
              layout={{
                'icon-image': 'compass',
                'icon-size': 0.25,
                'icon-rotate': 90,
                // 'icon-allow-overlap': true,
                'symbol-placement': 'line',
                'icon-rotation-alignment': 'map',
                'symbol-spacing': 20
              }}
              paint={{
                'icon-color': '#FFF'
              }}
            />
          )}
        </Source>
        {data && (
          <Source type='geojson' id='run-pairs' data={data.pairs}>
            <Layer
              id='run-pairs'
              type='line'
              layout={{
                'line-join': 'round',
                'line-cap': 'round'
              }}
              paint={{
                'line-color': [
                  'interpolate',
                  ['linear'],
                  ['get', 'speed'],
                  ...computeColors(
                    interpolateInferno,
                    data.pairs.properties.speed
                  )
                  // data.pairs.properties.speed[0],
                  // '#FF0000',
                  // data.pairs.properties.speed[1],
                  // '#0000FF'
                ],
                'line-width': 2
              }}
            />
          </Source>
        )}
        {kmMarks && (
          <Source type='geojson' id='km-marks' data={kmMarks}>
            <Layer
              id='km-marks-bg'
              type='circle'
              minzoom={13}
              paint={{
                'circle-radius': 8,
                'circle-stroke-color': '#0d2125',
                'circle-stroke-width': 1,
                'circle-color': [
                  'match',
                  ['get', 'label'],
                  'S',
                  '#095e86',
                  'F',
                  '#cd2b02',
                  '#FFF'
                ]
              }}
            />
            <Layer
              id='km-marks'
              type='symbol'
              minzoom={13}
              layout={{
                'text-field': ['get', 'label'],
                'text-size': 12,
                'text-allow-overlap': true
              }}
              paint={{
                'text-color': [
                  'match',
                  ['get', 'label'],
                  'S',
                  '#FFF',
                  'F',
                  '#FFF',
                  '#0d2125'
                ]
              }}
            />
          </Source>
        )}
      </Map>

      <RunDetails
        run={data}
        onCloseClick={() => setSelectedRun(null)}
        onTabChange={(v) => setSegmentType(v)}
      />

      <Fade in={status === 'loading'}>
        <Box
          position='absolute'
          inset={0}
          bg='rgba(255, 255, 255, 0.8)'
          display='flex'
          pointerEvents={status === 'loading' ? 'all' : 'none'}
          justifyContent='center'
          alignItems='center'
          textTransform='uppercase'
        >
          Loading
        </Box>
      </Fade>
    </Box>
  );
}

Component.displayName = 'Home';

function computeColors(colorFn, domain) {
  const colorScale = scaleSequential(colorFn);

  const [min, max] = domain;
  return colorScale
    .ticks()
    .flatMap((step) => [min + (max - min) * step, colorScale(step)]);
}
