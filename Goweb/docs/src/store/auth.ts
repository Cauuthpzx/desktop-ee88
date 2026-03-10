import { defineStore } from "pinia";
import api from "../utils/api";

interface User {
  id: number;
  username: string;
  created_at: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
}

export const useAuthStore = defineStore({
  id: "auth",
  state: (): AuthState => ({
    user: null,
    token: null,
  }),
  getters: {
    is_authenticated: (state) => !!state.token,
  },
  actions: {
    async login(username: string, password: string) {
      const res = await api.post("/api/auth/login", { username, password });
      this.user = res.data.data.user;
      this.token = res.data.data.token;
      localStorage.setItem("token", this.token!);
    },
    async register(username: string, password: string) {
      const res = await api.post("/api/auth/register", { username, password });
      this.user = res.data.data.user;
      this.token = res.data.data.token;
      localStorage.setItem("token", this.token!);
    },
    async change_password(old_password: string, new_password: string) {
      await api.post("/api/auth/change-password", { old_password, new_password });
    },
    async logout() {
      try {
        await api.post("/api/auth/logout");
      } finally {
        this.user = null;
        this.token = null;
        localStorage.removeItem("token");
      }
    },
  },
  persist: {
    enabled: true,
    strategies: [
      {
        key: "auth",
        storage: localStorage,
      },
    ],
  },
});
