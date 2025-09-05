// Utility class to handle localStorage operations similar to mobile app SharedPreferences
class SharedPref {
  static get token() {
    return localStorage.getItem('authToken') || '';
  }
  
  static set token(value) {
    if (value) {
      localStorage.setItem('authToken', value);
    } else {
      localStorage.removeItem('authToken');
    }
  }
  
  static get userData() {
    const data = localStorage.getItem('userData');
    return data ? JSON.parse(data) : null;
  }
  
  static set userData(value) {
    if (value) {
      localStorage.setItem('userData', JSON.stringify(value));
    } else {
      localStorage.removeItem('userData');
    }
  }
  
  static clear() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
  }
  
  // Get API headers for authenticated requests
  static getApiHeaders() {
    return {
      'Authorization': this.token ?? '',
      'Content-Type': 'application/json'
    };
  }
}

export default SharedPref;