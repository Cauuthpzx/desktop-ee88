<template>
  <div class="page-container">
    <div class="page-body">
      <lay-card>
        <template #body>
          <slot />
        </template>
      </lay-card>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  margin-top: 60px;
  min-height: calc(100vh - 60px);
  padding: 0;
  background: #f5f5f5;
}

.page-body {
  margin: 10px 10px 0 10px;
}
</style>
