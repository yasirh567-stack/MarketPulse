// `plotly.js-dist-min` ships no type declarations of its own; its runtime
// shape matches the full `plotly.js` package, which react-plotly.js already
// types against, so we simply hand off to `any` here rather than pull in
// (and maintain) a duplicate type surface for a pure runtime re-export.
declare module "plotly.js-dist-min" {
  const Plotly: any;
  export default Plotly;
}
