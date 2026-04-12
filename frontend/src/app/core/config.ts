import { isDevMode } from '@angular/core';

export const API_URL = isDevMode() 
  ? 'http://localhost:8000/api' 
  : 'https://appointmenk.onrender.com/api';
