export const setToken = (token: string) => localStorage.setItem("muelaads_token", token);
export const getToken = () => localStorage.getItem("muelaads_token");
export const removeToken = () => localStorage.removeItem("muelaads_token");
export const isAuthenticated = () => !!getToken();
