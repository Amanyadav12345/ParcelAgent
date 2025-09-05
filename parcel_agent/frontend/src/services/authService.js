import SharedPref from '../utils/SharedPref';

// Authentication service for managing user login and token storage
class AuthService {
  constructor() {
    this.token = SharedPref.token;
    this.userData = SharedPref.userData;
  }

  // Check if user is authenticated
  isAuthenticated() {
    return !!this.token;
  }

  // Get current user data
  getCurrentUser() {
    return this.userData;
  }

  // Get auth token
  getToken() {
    return this.token;
  }

  // Get API headers with authentication
  getAuthHeaders() {
    return SharedPref.getApiHeaders();
  }

  // Login user
  async login(username, password) {
    try {
      // Construct the API URL with exact encoding format as specified
      // Match: {%22$or%22:[{%22username%22:%22917340224449%22},{password%22:%2212345%22}]}
      const whereClause = `{%22$or%22:[{%22username%22:%22${username}%22},{%22password%22:%22${password}%22}]}`;
      
      const apiUrl = `https://35.244.19.78:8042/persons/authenticate?page=1&max_results=10&where=${whereClause}`;
      
      // Create Basic Auth token: base64(username:password)
      const credentials = `${username}:${password}`;
      const basicAuthToken = btoa(credentials);
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Basic ${basicAuthToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.ok && data.token) {
        // Store authentication data
        this.token = data.token;
        this.userData = data.user_record;
        
        SharedPref.token = data.token;
        SharedPref.userData = data.user_record;
        
        return { success: true, data };
      } else {
        return { 
          success: false, 
          error: data.statusText || 'Login failed. Please check your credentials.' 
        };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: 'Login failed. Please check your credentials and try again.' 
      };
    }
  }

  // Logout user
  logout() {
    this.token = null;
    this.userData = null;
    SharedPref.clear();
  }

  // Make authenticated API request
  async makeAuthenticatedRequest(url, options = {}) {
    const headers = {
      ...this.getAuthHeaders(),
      ...options.headers
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      // If unauthorized, logout user
      if (response.status === 401) {
        this.logout();
        window.location.reload();
        return null;
      }

      return response;
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }
}

// Create and export a singleton instance
const authService = new AuthService();
export default authService;