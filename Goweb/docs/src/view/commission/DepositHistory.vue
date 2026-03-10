<template>
  <PageLayout>
    <lay-field>
      <template #title>
        <span class="field-title">
          <lay-icon type="layui-icon-diamond" size="18px"></lay-icon>
          DANH SÁCH NẠP TIỀN
        </span>
      </template>

      <lay-form :model="searchForm" class="search-form" mode="inline" label-width="auto">
        <lay-form-item label="Thời gian tạo đơn：">
          <lay-date-picker
            v-model="searchForm.dateRange"
            type="date"
            range
            single-panel
            allow-clear
            :placeholder="['Thời gian bắt đầu', 'Thời gian kết thúc']"
          ></lay-date-picker>
        </lay-form-item>
        <lay-form-item label="Tên tài khoản：">
          <lay-input v-model="searchForm.username" placeholder="Nhập tên tài khoản" style="width: 300px"></lay-input>
        </lay-form-item>
        <lay-form-item label="Loại hình giao dịch：">
          <lay-select v-model="searchForm.type" placeholder="Chọn" allow-clear searchable style="width: 220px">
            <lay-select-option value="1" label="Nạp tiền"></lay-select-option>
            <lay-select-option value="2" label="Rút tiền"></lay-select-option>
          </lay-select>
        </lay-form-item>
        <lay-form-item label="Trạng thái giao dịch：">
          <lay-select v-model="searchForm.status" placeholder="Chọn" allow-clear searchable style="width: 180px">
            <lay-select-option value="0" label="Chờ xử lí"></lay-select-option>
            <lay-select-option value="1" label="Hoàn tất"></lay-select-option>
            <lay-select-option value="2" label="Đang xử lí"></lay-select-option>
            <lay-select-option value="3" label="Trạng thái không thành công"></lay-select-option>
          </lay-select>
        </lay-form-item>
        <lay-form-item>
          <lay-button type="primary" @click="handleSearch">
            <lay-icon type="layui-icon-search"></lay-icon> Tìm kiếm
          </lay-button>
          <lay-button @click="handleReset">
            <lay-icon type="layui-icon-refresh"></lay-icon> Đặt lại
          </lay-button>
        </lay-form-item>
      </lay-form>
    </lay-field>

    <lay-table :columns="columns" :data-source="tableData" :default-toolbar="['filter', 'export', 'print']" :page="pagination" @change="handlePageChange">
    </lay-table>
  </PageLayout>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import PageLayout from "../../components/PageLayout.vue";

const searchForm = reactive({
  dateRange: [] as string[],
  username: "",
  type: null as string | null,
  status: null as string | null,
});

const columns = ref([
  { title: "Tên tài khoản", key: "username" },
  { title: "Thuộc đại lý", key: "user_parent_format" },
  { title: "Số tiền", key: "amount" },
  { title: "Loại hình giao dịch", key: "type" },
  { title: "Trạng thái giao dịch", key: "status" },
  { title: "Thời gian tạo đơn", key: "create_time" },
]);

const tableData = ref([] as any[]);

const pagination = reactive({
  current: 1,
  limit: 10,
  total: 1,
  limits: [10, 20, 30, 40, 50, 60, 70, 80, 90],
  layout: ["prev", "page", "next", "skip", "count", "limit"],
});

function handleSearch() {
  console.log("search", searchForm);
}

function handleReset() {
  searchForm.dateRange = [];
  searchForm.username = "";
  searchForm.type = null;
  searchForm.status = null;
}

function handlePageChange(page: any) {
  pagination.current = page.current;
  pagination.limit = page.limit;
}
</script>

<style scoped>
.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.field-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 700;
}
</style>
