<template>
  <q-btn dense round color="green-14" icon="upload_file" @click="triggerPickFiles" />
  <q-uploader
    multiple
    ref="fileUploader"
    accept=".json, .geojson, .kml, .tif, .tiff"
    class="hidden"
    @added="addedFiles"
  >
  </q-uploader>
</template>

<script>
import { ref } from 'vue'
import { datasetApi } from 'src/services/api'
import { useQuasar } from 'quasar'

export default {
  name: 'FileUploader',
  props: {},
  emits: ['fileUploaded'],
  setup(props, { emit }) {
    const fileUploader = ref(null)
    const $q = useQuasar()

    return {
      triggerPickFiles: () => {
        fileUploader.value.pickFiles()
      },
      fileUploader,
      async addedFiles(files) {
        const unsupportedExtensions = ['.tif', '.tiff']
        const unsupportedFiles = []
        const validFiles = []

        // Separate valid and unsupported files in one iteration
        files.forEach((file) => {
          const extension = file.name.split('.').pop().toLowerCase()
          if (unsupportedExtensions.includes(`.${extension}`)) {
            unsupportedFiles.push(file.name)
          } else {
            validFiles.push(file)
          }
        })

        // Notify about unsupported files
        if (unsupportedFiles.length) {
          $q.notify({
            message: `Sorry, TIFF files are not supported yet: ${unsupportedFiles.join(', ')}`,
            color: 'warning',
            icon: 'warning',
          })
        }

        // Proceed with uploading valid files
        if (validFiles.length) {
          try {
            await Promise.all(
              validFiles.map((file) =>
                datasetApi
                  .upload(file, file.name)
                  .then((response) => emit('fileUploaded', response.data)),
              ),
            )
          } catch (e) {
            console.error('Error uploading files:', e)
          }
        }

        // Reset the file uploader
        fileUploader.value.reset()
      },
    }
  },
}
</script>

<style lang="scss" scoped></style>
