<template>
  <q-page>
    <div id="world-map"></div>
    <div v-if="hoverInfo" class="hover-card" :style="getHoverCardStyle">
      <div class="hover-card-content">
        <div class="title q-my-xs">Shape Information</div>
        <div v-if="!isNaN(hoverInfo.id)"><span class="bold">id:</span> {{ hoverInfo.id }}</div>
        <div><span class="bold">Type:</span> {{ hoverInfo.type }}</div>
        <template v-if="hoverInfo.properties">
          <div v-if="hoverInfo.properties.created_at" class="text-body2">
            <span class="bold">Created:</span> {{ formatDate(hoverInfo.properties.created_at) }}
          </div>
          <div v-if="hoverInfo.properties.updated_at" class="text-body2">
            <span class="bold">Updated:</span> {{ formatDate(hoverInfo.properties.updated_at) }}
          </div>
        </template>
      </div>
    </div>
    <div class="absolute-top-right custom-bar q-ma-xs">
      <LogoutButton />
      <FileUploader @fileUploaded="renderFile" />
      <q-btn color="primary" label="Dataset Files" no-caps>
        <q-menu :offset="[10, 10]">
          <q-list bordered separator class="bg-white">
            <q-item v-if="datasets.length === 0">No files are uploaded yet</q-item>
            <q-item v-for="dataset in datasets" :key="dataset.id" clickable v-ripple>
              <q-item-section avatar>
                <q-checkbox
                  v-model="dataset.visibility"
                  @update:model-value="toggleDatasetVisibility(dataset)"
                  :disable="dataset.processing"
                />
              </q-item-section>

              <q-item-section>
                <q-item-label>{{ dataset.name }}</q-item-label>
                <q-item-label caption>{{ dataset.file_type.toUpperCase() }}</q-item-label>
              </q-item-section>

              <q-item-section side>
                <q-btn flat round icon="delete" color="negative" @click="deleteDataset(dataset)" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>
    </div>
  </q-page>
</template>

<script>
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useQuasar } from 'quasar'
import RulerControl from '@mapbox-controls/ruler'
import '@mapbox-controls/ruler/src/index.css'
import MapboxDraw from '@mapbox/mapbox-gl-draw'
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css'
import { shapeApi } from 'src/services/api'
import FileUploader from 'components/FileUploader.vue'
import { datasetApi } from 'src/services/api'
import { MapDataManager } from 'src/helpers/mapHelpers'
import LogoutButton from 'components/LogoutButton.vue'

export default {
  components: { FileUploader, LogoutButton },
  setup() {
    let map = null

    let draw = null
    const hoverInfo = ref(null)
    const hoverCoordinates = ref(null)
    const datasets = ref([])
    const $q = useQuasar()

    const formatDate = (isoString) => {
      const date = new Date(isoString)
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date)
    }

    const fetchDatasets = async () => {
      try {
        const response = await datasetApi.list()
        datasets.value = response.data.map((dataset) => ({
          ...dataset,
          visibility: false,
        }))
      } catch (error) {
        console.log(error)
        $q.notify({
          color: 'negative',
          message: 'Failed to load datasets',
          icon: 'warning',
        })
      }
    }

    const toggleDatasetVisibility = async (dataset) => {
      dataset.processing = true
      try {
        await MapDataManager.setDatasetVisibility(map, dataset, dataset.visibility)
      } catch (error) {
        console.log(error)
        // Revert the checkbox if the API call fails
        dataset.visibility = !dataset.visibility
        $q.notify({
          color: 'negative',
          message: 'Failed to update dataset visibility',
          icon: 'warning',
        })
      } finally {
        dataset.processing = false
      }
    }

    const initializeDraw = () => {
      draw = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
          polygon: true,
          line_string: true,
          point: true,
          trash: true,
        },
        styles: [
          // Polygon fill
          {
            id: 'gl-draw-polygon-fill',
            type: 'fill',
            filter: ['all', ['==', '$type', 'Polygon']],
            paint: {
              'fill-color': '#ff69b4',
              'fill-outline-color': '#ff69b4',
              'fill-opacity': 0.2,
            },
          },
          // Polygon stroke
          {
            id: 'gl-draw-polygon-stroke',
            type: 'line',
            filter: ['all', ['==', '$type', 'Polygon']],
            paint: {
              'line-color': '#ff69b4',
              'line-width': 2,
            },
          },
          // Line string
          {
            id: 'gl-draw-line',
            type: 'line',
            filter: ['all', ['==', '$type', 'LineString']],
            paint: {
              'line-color': '#1e90ff',
              'line-width': 2,
            },
          },
          // Point marker
          {
            id: 'gl-draw-point',
            type: 'circle',
            filter: ['all', ['==', '$type', 'Point']],
            paint: {
              'circle-radius': 5,
              'circle-color': '#32cd32',
            },
          },
          // Active polygon stroke
          {
            id: 'gl-draw-polygon-and-line-vertex-halo-active',
            type: 'circle',
            filter: [
              'all',
              ['==', 'meta', 'vertex'],
              ['==', '$type', 'Point'],
              ['!=', 'mode', 'static'],
            ],
            paint: {
              'circle-radius': 9, // Larger halo for active vertex
              'circle-color': '#ffffff', // White for contrast
            },
          },
          // Active polygon vertex
          {
            id: 'gl-draw-polygon-and-line-vertex-active',
            type: 'circle',
            filter: [
              'all',
              ['==', 'meta', 'vertex'],
              ['==', '$type', 'Point'],
              ['!=', 'mode', 'static'],
            ],
            paint: {
              'circle-radius': 6, // Visible active vertex
              'circle-color': '#ff4500', // Orange red for visibility
            },
          },
        ],
      })
    }

    // Load saved shapes from backend
    const loadSavedShapes = async () => {
      try {
        const response = await shapeApi.list()
        draw.set({
          type: 'FeatureCollection',
          features: response.data,
        })
      } catch (error) {
        console.error('Error loading shapes:', error)
      }
    }

    // Save drawn shape
    const saveShape = async (e) => {
      const feature = e.features[0]
      // console.log('create:', feature)
      try {
        const response = await shapeApi.create({
          ...feature,
          properties: {
            ...feature.properties,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        })
        draw.delete(feature.id)
        draw.add({ ...response.data })
        selectedFeatureId = null
      } catch (error) {
        console.error('Error saving shape:', error)
      }
    }

    // Update existing shape
    const updateShape = async (e) => {
      const feature = e.features[0]
      // console.log('update:', feature)
      try {
        const response = await shapeApi.update(feature.id, {
          ...feature,
          properties: {
            ...feature.properties,
            updated_at: new Date().toISOString(),
          },
        })
        // replace existing feature
        draw.add({ ...response.data })
      } catch (error) {
        console.error('Error updating shape:', error)
      }
    }

    const clearHover = () => {
      hoverInfo.value = null
      hoverCoordinates.value = null
    }

    // Delete shape
    const deleteShape = async (e) => {
      const feature = e.features[0]
      // console.log('delete:', feature)
      try {
        await shapeApi.delete(feature.id)
        selectedFeatureId = null
      } catch (error) {
        console.error('Error deleting shape:', error)
      }
    }

    onUnmounted(() => {
      if (map && draw) {
        map.removeControl(draw)
      }
    })

    const initMap = () => {
      mapboxgl.accessToken = process.env.MAPBOX_ACCESS_TOKEN

      map = new mapboxgl.Map({
        container: 'world-map', // container ID
        center: [-74.5, 40], // starting position [lng, lat]. Note that lat must be set between -90 and 90
        zoom: 9, // starting zoom
      })

      map.on('mousemove', (e) => {
        // Get features under the mouse
        const featureIds = draw.getFeatureIdsAt(e.point)
        if (typeof featureIds[0] === 'number') {
          const feature = draw.get(featureIds[0])
          // console.log(feature.id, draw.getMode(), selectedFeatureId)
          if (typeof selectedFeatureId !== 'string' && feature.id !== selectedFeatureId) {
            hoverCoordinates.value = e.lngLat
            // Store feature info for display
            hoverInfo.value = {
              id: feature.id,
              type: feature.geometry.type,
              properties: feature.properties,
            }
            return
          }
        }
        clearHover()
      })

      map.on('load', () => {
        fetchDatasets()
        const rulerControl = new RulerControl()
        map.addControl(rulerControl, 'bottom-right')

        initializeDraw()
        map.addControl(draw, 'top-left')

        // Load saved shapes
        loadSavedShapes()

        // Add event listeners
        map.on('draw.create', saveShape)
        map.on('draw.update', updateShape)
        map.on('draw.delete', deleteShape)

        map.on('draw.selectionchange', (e) => {
          // console.log('selected features:', e.features)
          if (e.features.length) {
            selectedFeatureId = e.features[0].id
            clearHover()
          } else {
            selectedFeatureId = null
          }
        })
      })
    }

    let selectedFeatureId = null

    const renderFile = async (dataset) => {
      try {
        await MapDataManager.addDataset(map, dataset)
        datasets.value.push({ ...dataset, visibility: true })
      } catch {
        datasets.value.push({ ...dataset, visibility: false })
      }
    }

    const getHoverCardStyle = computed(() => {
      if (!hoverCoordinates.value) return {}

      // Convert map coordinates to pixel coordinates
      const point = map.project(hoverCoordinates.value)

      return {
        left: `${point.x + 10}px`, // Offset from cursor
        top: `${point.y + 10}px`,
      }
    })

    const deleteDataset = async (dataset) => {
      dataset.processing = true
      try {
        await datasetApi.delete(dataset.id)
        MapDataManager.removeDataset(map, dataset.id)
        datasets.value = datasets.value.filter((d) => d.id !== dataset.id)

        $q.notify({
          color: 'positive',
          message: 'Dataset deleted successfully',
          icon: 'check',
        })
      } catch {
        $q.notify({
          color: 'negative',
          message: 'Failed to delete dataset',
          icon: 'warning',
        })
        dataset.processing = false
      }
    }

    onMounted(() => {
      initMap()
    })

    return {
      deleteDataset,
      formatDate,
      map,
      hoverCoordinates,
      hoverInfo,
      getHoverCardStyle,
      renderFile,
      datasets,
      toggleDatasetVisibility,
    }
  },
}
</script>

<style lang="scss">
#world-map {
  height: 100vh;
  width: 100vw;
}

.bold {
  font-weight: 500;
}
.hover-card {
  position: fixed;
  background: white;
  border-radius: 4px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  // pointer-events: none;
  z-index: 1000;
  max-width: 250px;

  .hover-card-content {
    font-size: 14px;

    .title {
      font-size: 17px;
      font-weight: 600;
    }
  }
}

.hover-card h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
}

.hover-card p {
  margin: 4px 0;
}

.custom-bar {
  display: flex;
  gap: 8px;
}
</style>
