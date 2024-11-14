import React, { useEffect, useState } from 'react';
import DeckGL from '@deck.gl/react';
import { OrbitView, COORDINATE_SYSTEM } from '@deck.gl/core';
import { PointCloudLayer, PathLayer } from '@deck.gl/layers';
import type { OrbitViewState } from '@deck.gl/core';
import * as d3 from 'd3';
import { Layer, Map, Source, useControl } from 'react-map-gl';
import { MapboxOverlay } from '@deck.gl/mapbox/dist/es5/index.js';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Box } from '@chakra-ui/react';

const INITIAL_VIEW_STATE: OrbitViewState = {
  target: [500, 500, 0],
  rotationX: 45,
  rotationOrbit: 0,
  minZoom: 0,
  maxZoom: 10,
  zoom: 0.5
};

const data2 = [
  {
    position: [0, 0, 0],
    color: [255, 0, 0]
  },
  {
    position: [10, 0, 0],
    color: [0, 255, 0]
  },
  {
    position: [0, 10, 0],
    color: [0, 0, 255]
  }
];

function rgb2array(hex: string) {
  return hex
    .substring(1)
    .match(/.{2}/g)!
    .map((v) => parseInt(v, 16));
}

async function prepareData(filename: string): Promise<PointData[]> {
  const response = await fetch(filename);
  const raw = await response.text();
  const data = raw
    .split('\n')
    .map((line) => line.split(',').map((v) => Number(v)))
    .slice(1, -1);

  const values = data.map((d) => d[2]);

  const [min, max] = d3.extent(values) as [number, number];

  const color = d3.scaleSequential([min, max], d3.interpolateViridis);
  const alpha = d3.scaleLinear([min, max * 0.25], [0, 198]).clamp(true);

  return data.map(([, , v, lon, lat]) => ({
    position: [lon, lat, 0],
    val: v,
    color: [...rgb2array(color(v)), alpha(v)]
  }));
}

function DeckGLOverlay(props) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

interface PointData {
  position: number[];
  color: number[];
  val: number;
}

export function Component() {
  const [viewState, updateViewState] =
    useState<OrbitViewState>(INITIAL_VIEW_STATE);

  const [data, setData] = useState<PointData[]>([]);
  const [lineData, setLineData] = useState<number[][]>([]);

  useEffect(() => {
    async function load() {
      const maxIndexes: number[] = [];
      const allData: PointData[][] = [];

      await Promise.all(
        Array(28)
          .fill(0)
          .map(async (_, i) => {
            const data = await prepareData(
              `/AD_A11177/AD_A11177_states_${i}.csv`
            );
            const max = d3.maxIndex(data, (d) => d.val);
            allData.push(data);
            maxIndexes.push(max);
            console.log('loaded', i);
          })
      );

      // Circulate over data
      function showData(index) {
        setData(allData[index]);

        // prepare line data
        if (index === 0) {
          setLineData([]);
        } else {
          const line = maxIndexes
            .slice(0, index + 1)
            .map((maxInd, i) => {
              const [x, y] = allData[i][maxInd].position;
              return [x, y, 1000];
            })
            .slice(-4);
          setLineData(line);
        }
      }
      let count = 0;
      setInterval(() => {
        showData(count % allData.length);
        count++;
      }, 500);
    }
    // load();
  }, []);

  // const layers = [
  //   new PointCloudLayer({
  //     id: 'point-cloud-layer',
  //     data,
  //     getNormal: [0, 1, 0],
  //     getColor: (d) => d.color,
  //     getPosition: (d) => d.position,
  //     coordinateOrigin: [0, 0, 0],
  //     coordinateSystem: COORDINATE_SYSTEM.DEFAULT,
  //     pointSize: 0.8,
  //     sizeUnits: 'meters'
  //   }),
  //   new PathLayer({
  //     id: 'PathLayer',
  //     data: [{ path: lineData }],
  //     getColor: (d) => [255, 0, 0],
  //     getPath: (d) => d.path,
  //     jointRounded: true,
  //     capRounded: true,
  //     getWidth: 0.5
  //   })
  // ];
  const layers = [
    new PointCloudLayer({
      id: 'point-cloud-layer',
      data,
      getNormal: [0, 1, 0],
      getColor: (d) => d.color,
      // getColor: (d) => [...d.color, 128],
      getPosition: (d) => d.position,
      // coordinateOrigin: [0, 0, 0],
      // coordinateSystem: COORDINATE_SYSTEM.DEFAULT,
      pointSize: 0.018,
      sizeUnits: 'common'
    }),
    new PathLayer({
      id: 'PathLayer',
      data: [{ path: lineData }],
      getColor: (d) => [255, 0, 0],
      getPath: (d) => d.path,
      jointRounded: true,
      capRounded: true,
      getWidth: 500
    })
  ];

  const [viewStateMap, setViewState] = useState({
    longitude: -10,
    latitude: 40,
    zoom: 6,
    pitch: 0
  });

  return (
    // <DeckGL
    //   views={new OrbitView()}
    //   initialViewState={viewState}
    //   controller={true}
    //   layers={layers}
    // />

    <Box position='absolute' inset={0}>
      <Map
        {...viewStateMap}
        mapboxAccessToken={process.env.MAPBOX_TOKEN!}
        onMove={(evt) => setViewState(evt.viewState)}
        mapStyle='mapbox://styles/devseed/clwj0j1af00hy01pc4n33aq16'
      >
        <Source
          type='raster'
          id='bathymetry'
          tiles={[
            'https://tiles.emodnet-bathymetry.eu/2020/baselayer/web_mercator/{z}/{x}/{y}.png'
          ]}
        >
          <Layer type='raster' id='bathymetry' beforeId='country-boundaries' />
        </Source>

        <DeckGLOverlay layers={layers} />
      </Map>
    </Box>
  );
}
