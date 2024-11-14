import React, { useEffect, useRef, useState } from 'react';
import { PointCloudLayer, PathLayer } from '@deck.gl/layers';
import * as d3 from 'd3';
import { Layer, Map as ReactMap, Source, useControl } from 'react-map-gl';
import { MapboxOverlay } from '@deck.gl/mapbox/dist/es5/index.js';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Box, Flex } from '@chakra-ui/react';
import { button, useControls } from 'leva';
import { PointData, prepareData, rgb2array } from './utils';

/**
 * Component to add deck GL overlay to the map.
 */
function DeckGLOverlay(props) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

/**
 * Main Page component.
 */
export function Component() {
  const playCount = useRef(0);
  const [rawData, setRawData] = useState<number[][][]>();
  const [loadedData, setLoadedData] = useState<
    {
      data: PointData[];
      maxIndex: number;
    }[]
  >();

  // Data to be displayed
  const [data, setData] = useState<PointData[]>();
  // Line data to be displayed
  const [lineData, setLineData] = useState<number[][]>();

  const [inputTag, setInputTag] = useState('A19124');
  const [selectedTag, setSelectedTag] = useState('');
  // START debug controls definition
  const { isRunning, fps } = useControls(
    {
      dataTag: {
        value: inputTag,
        onChange: (v) => setInputTag(v)
      },
      load: button(() => {
        if (inputTag === selectedTag) return;
        setSelectedTag(inputTag);
        setRawData(undefined);
      }),
      isRunning: {
        label: 'Running',
        value: false
      },
      fps: {
        value: 10,
        min: 1,
        step: 1,
        max: 60
      }
    },
    [inputTag, selectedTag]
  );

  const { pointSize } = useControls('Point controls', {
    pointSize: {
      label: 'Point(^-3)',
      value: 18,
      min: 1,
      step: 1,
      max: 100
    }
  });

  const { tailLength, tailWidth, tailColor } = useControls('Tail controls', {
    tailLength: {
      value: 4,
      min: 1,
      step: 1,
      max: 20
    },
    tailWidth: {
      value: 1000,
      min: 1,
      step: 1,
      max: 5000
    },
    tailColor: '#54d0f2'
  });

  // The refresh state is used to force a refresh of the data when the user
  // changes the controls, otherwise there would be too many changes and the app
  // would crash.
  const [refreshed, refresh] = useState<number>();
  const dataValues = useControls('Data controls', {
    warning: {
      label: '⚠️ Warning',
      value:
        'Changing these values will cause the data to be reprocessed.\nIt will freeze the app for a few seconds.',
      editable: false,
      rows: true
    },
    percentile: {
      value: 95,
      min: 1,
      step: 0.1,
      max: 100,
      onEditEnd: () => refresh(Date.now())
    },
    alphaMax: {
      value: 0.8,
      min: 0,
      step: 0.01,
      max: 1,
      onEditEnd: () => refresh(Date.now())
    },
    alphaRescale: {
      value: [0, 0.25],
      min: 0,
      step: 0.01,
      max: 1,
      onEditEnd: () => refresh(Date.now())
    }
  });
  // END debug controls definition.

  // Load data from file in the /static folder.
  useEffect(() => {
    async function load() {
      const file = `/${selectedTag}_states.csv`;

      // eslint-disable-next-line
      console.time('Load Data');
      const response = await fetch(file);
      const raw = await response.text();
      // eslint-disable-next-line
      console.timeEnd('Load Data');

      // eslint-disable-next-line
      console.time('Process Data');
      const timesteps = raw.split('\n\n').slice(0, -1);

      const result = timesteps.map((timestep) => {
        const lines = timestep
          .split('\n')
          .map((line) => line.split(',').map((v) => Number(v)));
        return lines;
      });
      setRawData(result);
      // eslint-disable-next-line
      console.timeEnd('Process Data');
      // eslint-disable-next-line
      console.log('✨ All loaded');
    }
    if (!rawData?.length && selectedTag) {
      load();
    }
  }, [rawData, selectedTag]);

  // Process the data after it is loaded and when the controls are changed.
  useEffect(() => {
    if (!rawData) {
      return;
    }

    // eslint-disable-next-line
    console.time('prepareData');
    const result = rawData.map((lines) => {
      const data = prepareData(
        lines,
        dataValues.percentile,
        dataValues.alphaRescale,
        dataValues.alphaMax * 255
      );
      const max = d3.maxIndex(data, (d) => d.val);

      return {
        data,
        maxIndex: max
      };
    });

    // eslint-disable-next-line
    console.timeEnd('prepareData');

    setLoadedData(result);
  }, [rawData, refreshed]);

  // Display the data on the map.
  useEffect(() => {
    if (!loadedData) {
      return;
    }

    // Circulate over data
    function showData(index) {
      setData(loadedData![index].data);

      // Prepare line data
      if (index === 0) {
        setLineData([]);
      } else {
        const line = loadedData!
          .slice(Math.max(index - tailLength, 0), index + 1)
          .map(({ data, maxIndex }) => {
            const [x, y] = data[maxIndex].position;
            return [x, y, 1000];
          });
        setLineData(line);
      }
    }

    showData(playCount.current % loadedData!.length);

    let prev = null;
    let rafId;
    function loop(ts) {
      if (prev !== null) {
        if (ts - prev > 1000 / fps) {
          showData(playCount.current % loadedData!.length);
          playCount.current++;
          prev = ts;
        }
      } else {
        prev = ts;
      }
      rafId = requestAnimationFrame(loop);
    }

    rafId = isRunning && requestAnimationFrame(loop);
    return () => rafId && cancelAnimationFrame(rafId);
  }, [fps, tailLength, isRunning, loadedData]);

  const layers = [
    new PointCloudLayer({
      id: 'point-cloud-layer',
      data,
      getNormal: [0, 1, 0],
      getColor: (d) => d.color,
      getPosition: (d) => d.position,
      pointSize: pointSize / 1000,
      sizeUnits: 'common'
    }),
    new PathLayer({
      id: 'data-tail',
      data: [{ path: lineData }],
      getColor: rgb2array(tailColor),
      getPath: (d) => d.path,
      jointRounded: true,
      capRounded: true,
      getWidth: tailWidth
    })
  ];

  const [viewStateMap, setViewState] = useState({
    longitude: -3.4742,
    latitude: 46.64983,
    zoom: 6,
    pitch: 0
  });

  return !rawData?.length ? (
    <Flex
      h='100vh'
      alignItems='center'
      justifyContent='center'
      direction='column'
    >
      {selectedTag ? (
        <>
          <p>Loading data...</p>
          <p>There&apos;s a lot of it. Be patient!</p>
        </>
      ) : (
        <p>Set a tag and press load</p>
      )}
    </Flex>
  ) : (
    <Box position='absolute' inset={0}>
      <ReactMap
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
      </ReactMap>
    </Box>
  );
}
