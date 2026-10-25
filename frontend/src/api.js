const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://trustvault-backend-b3uo.onrender.com'

export async function apiRequest(path, options = {}, token = null) {
    const headers = { ...options.headers }
    
    if (token) {
        headers.Authorization = `Bearer ${token}`
    }

    if (
        options.body &&
        !(options.body instanceof FormData) &&
        !headers['Content-Type']
    ) {
        headers['Content-Type'] = 'application/json'
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
    })

    const contentType = response.headers.get('content-type') || ''
    const data = contentType.includes('application/json')
        ? await response.json()
        : await response.text()

    if (!response.ok) {
        const message =
            typeof data === 'object' && data !== null
                ? data.detail || `Request failed (${response.status})`
                : data || `Request failed (${response.status})`

        throw new Error(message)
    }

    return data
}

export async function login(username, password) {
    const body = new URLSearchParams({ username, password })

    const result = await apiRequest('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body,
    })

    if (!result.access_token) {
        throw new Error('The server did not return an access token.')
    }

    return result
}