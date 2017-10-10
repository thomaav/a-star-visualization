# A* visualizer

A script for creating gifs visualizing the A*-algorithm written in Python.

## Usage

The script uses ImageMagick's convert to create gifs from images, and can be invoked as such:
```
a-star-visualize <board> <out_file>
```

## Examples

Simple pathfinding in a graph that has no weighted edges:

![Alt Text](https://github.com/thomaav/a-star-visualization/raw/master/example_gifs/no-costs.gif)

With weights:

![Alt Text](https://github.com/thomaav/a-star-visualization/raw/master/example_gifs/with-costs.gif)