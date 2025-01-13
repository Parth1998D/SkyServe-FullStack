import { api } from 'boot/axios'

export const authApi = {
  login: (credentials) => {
    const formData = new URLSearchParams()
    formData.append('username', credentials.email) // FastAPI expects 'username'
    formData.append('password', credentials.password)

    // Send as form data with correct content type
    return api.post('/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },

  register: (credentials) =>
    api.post('/users', {
      email: credentials.email,
      password: credentials.password,
    }),
}

export const datasetApi = {
  // Upload a file with name
  upload: (file, name) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)
    return api.post('/datasets', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // List all datasets
  list: () => api.get('/datasets'),

  // Download a specific dataset
  download: (datasetId) =>
    api.get(`/datasets/${datasetId}/download`, {
      responseType: 'blob', // Important for file downloads
    }),

  // Delete a dataset
  delete: (datasetId) => api.delete(`/datasets/${datasetId}`),

  // Get details of a specific dataset
  getDetails: (datasetId) => api.get(`/datasets/${datasetId}`),
}
export const shapeApi = {
  list: () => api.get('/shapes'),

  create: (shape) => api.post('/shapes', shape),

  update: (id, shape) => api.put(`/shapes/${id}`, shape),

  delete: (id) => api.delete(`/shapes/${id}`),
}

export const markerApi = {
  create: (marker) => api.post('/markers', marker),

  update: (id, marker) => api.put(`/markers/${id}`, marker),

  delete: (id) => api.delete(`/markers/${id}`),
}
