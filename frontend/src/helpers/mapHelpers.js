// mapHelpers.js
import mapboxgl from 'mapbox-gl'
import * as toGeoJSON from '@mapbox/togeojson'
import { datasetApi } from 'src/services/api'

export const MapDataManager = {
  // Keep track of loaded datasets
  loadedDatasets: new Map(),

  async addDataset(map, dataset) {
    try {
      const response = await datasetApi.download(dataset.id)
      let geojsonData = null
      if (dataset.file_type === 'geojson') {
        geojsonData = await JSON.parse(await response.data.text())
      } else if (dataset.file_type === 'kml') {
        const kmlText = await response.data.text()
        const parser = new DOMParser()
        const kmlDoc = parser.parseFromString(kmlText, 'text/xml')
        geojsonData = toGeoJSON.kml(kmlDoc)
      }
      if (geojsonData) {
        this.addGeoJSON(map, dataset, geojsonData)
      }
    } catch (error) {
      console.error('Error adding GeoJSON dataset:', error)
    }
  },

  // Add or update a GeoJSON dataset to the map
  addGeoJSON(map, dataset, geojsonData) {
    try {
      this.removeDataset(map, dataset.id)

      // Add the source
      map.addSource(`dataset-${dataset.id}`, {
        type: 'geojson',
        data: geojsonData,
      })

      // Add layer for polygons/multipolygons
      map.addLayer({
        id: `dataset-fill-${dataset.id}`,
        type: 'fill',
        source: `dataset-${dataset.id}`,
        filter: [
          'any',
          ['==', ['geometry-type'], 'Polygon'],
          ['==', ['geometry-type'], 'MultiPolygon'],
        ],
        paint: {
          'fill-color': '#088',
          'fill-opacity': 0.5,
        },
      })

      // Add layer for line features
      map.addLayer({
        id: `dataset-line-${dataset.id}`,
        type: 'line',
        source: `dataset-${dataset.id}`,
        filter: [
          'any',
          ['==', ['geometry-type'], 'LineString'],
          ['==', ['geometry-type'], 'MultiLineString'],
          ['==', ['geometry-type'], 'Polygon'],
          ['==', ['geometry-type'], 'MultiPolygon'],
        ],
        paint: {
          'line-color': '#088',
          'line-width': 2,
        },
      })

      // Add layer for point features
      map.addLayer({
        id: `dataset-point-${dataset.id}`,
        type: 'circle',
        source: `dataset-${dataset.id}`,
        filter: [
          'any',
          ['==', ['geometry-type'], 'Point'],
          ['==', ['geometry-type'], 'MultiPoint'],
        ],
        paint: {
          'circle-radius': 5,
          'circle-color': '#088',
        },
      })

      // Store reference to dataset
      this.loadedDatasets.set(dataset.id, {
        type: 'geojson',
        layerIds: [
          `dataset-fill-${dataset.id}`,
          `dataset-line-${dataset.id}`,
          `dataset-point-${dataset.id}`,
        ],
      })

      this.addHoverInteractions(map, dataset.id)
    } catch (error) {
      console.error('Error adding GeoJSON dataset:', error)
    }
  },

  // Remove a dataset from the map
  removeDataset(map, datasetId) {
    const dataset = this.loadedDatasets.get(datasetId)
    if (dataset) {
      // Remove layers
      dataset.layerIds.forEach((layerId) => {
        if (map.getLayer(layerId)) {
          map.removeLayer(layerId)
        }
      })

      // Remove source
      if (map.getSource(`dataset-${datasetId}`)) {
        map.removeSource(`dataset-${datasetId}`)
      }

      // Remove from tracking
      this.loadedDatasets.delete(datasetId)
    }
  },

  // Set dataset visibility
  async setDatasetVisibility(map, dataset, isVisible) {
    const loadedDataset = this.loadedDatasets.get(dataset.id)
    if (loadedDataset) {
      const visibility = isVisible ? 'visible' : 'none'
      loadedDataset.layerIds.forEach((layerId) => {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, 'visibility', visibility)
        }
      })
    } else if (isVisible) {
      await this.addDataset(map, dataset)
    }
  },

  // Add hover interactions for the dataset
  addHoverInteractions(map, datasetId) {
    const dataset = this.loadedDatasets.get(datasetId)
    if (!dataset) return

    // Change cursor to pointer when hovering over features
    dataset.layerIds.forEach((layerId) => {
      map.on('mouseenter', layerId, () => {
        map.getCanvas().style.cursor = 'pointer'
      })

      map.on('mouseleave', layerId, () => {
        map.getCanvas().style.cursor = ''
      })
    })

    // Add popup for feature properties
    const popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
    })

    dataset.layerIds.forEach((layerId) => {
      map.on('mousemove', layerId, (e) => {
        if (e.features.length > 0) {
          const feature = e.features[0]
          const properties = feature.properties

          // Limit to maximum of 4 properties
          const limitedProperties = Object.entries(properties).slice(0, 4)

          // Create HTML content for popup
          const html = limitedProperties
            .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
            .join('<br>')

          popup.setLngLat(e.lngLat).setHTML(html).addTo(map)
        }
      })

      map.on('mouseleave', layerId, () => {
        popup.remove()
      })
    })
  },
}
