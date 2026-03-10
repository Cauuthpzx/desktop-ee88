import {
  createRouter as _createRouter,
  createWebHistory,
  NavigationGuardNext,
  RouteLocationNormalized,
  Router,
} from "vue-router";
import zhCN from "./zh-CN";
// @ts-ignore
import NProgress from "nprogress";
import "nprogress/nprogress.css";

const routes = [...zhCN];

export function createRouter(): Router {
  const router = _createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: routes,
  });

  router.beforeEach(
    (
      to: RouteLocationNormalized,
      from: RouteLocationNormalized,
      next: NavigationGuardNext
    ) => {
      NProgress.start();
      const token = localStorage.getItem("token");
      const requires_auth = to.matched.some((r) => r.meta.requires_auth);

      if (requires_auth && !token) {
        next("/login");
      } else if ((to.path === "/login" || to.path === "/register") && token) {
        next("/");
      } else {
        next();
      }
    }
  );

  router.afterEach(() => {
    NProgress.done();
  });

  return router;
}
