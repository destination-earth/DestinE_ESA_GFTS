import * as d3 from 'd3';

export interface PointData {
  position: number[];
  color: number[];
  extent: [number, number];
  val: number;
}

export function rgb2array(hex: string) {
  return hex
    .substring(1)
    .match(/.{2}/g)!
    .map((v) => parseInt(v, 16));
}


function getColor(value, extent, alphaRescale, alphaMax = 255) {
  const color = d3.scaleSequential(extent, d3.interpolateViridis);
  const [low, high] = alphaRescale;
  const [min, max] = extent;
  const diff = max - min;

  const alpha = d3
    .scaleLinear([min + diff * low, max - diff * (1 - high)], [0, alphaMax])
    .clamp(true);

  return [...rgb2array(color(value)), alpha(value)];
}

export function prepareData(
  rawData: number[][],
  percentile,
  alphaRescale,
  alphaMax
): PointData[] {
  const extent = d3.extent(rawData, (d) => d[0]) as [number, number];
  const [min, max] = extent;
  const diff = max - min;
  const threshold = min + diff * (1 - percentile / 100);

  return rawData
    .filter(([v]) => v > threshold)
    .map(([v, lon, lat]) => ({
      position: [lon, lat, 0],
      val: v,
      extent,
      color: getColor(v, extent, alphaRescale, alphaMax)
    }));
}
