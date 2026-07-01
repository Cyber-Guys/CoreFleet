import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: 'Dashboard' },
  },
  {
    path: '/vehicles',
    name: 'vehicles',
    component: () => import('@/views/VehiclesView.vue'),
    meta: { title: 'Vehicles' },
  },
  {
    path: '/drivers',
    name: 'drivers',
    component: () => import('@/views/DriversView.vue'),
    meta: { title: 'Drivers' },
  },
  {
    path: '/network',
    name: 'network',
    component: () => import('@/views/NetworkAnalysisView.vue'),
    meta: { title: 'Network Analysis' },
  },
  {
    path: '/reports',
    name: 'reports',
    component: () => import('@/views/ReportsView.vue'),
    meta: { title: 'Reports' },
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('@/views/AboutView.vue'),
    meta: { title: 'About Us' },
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})
