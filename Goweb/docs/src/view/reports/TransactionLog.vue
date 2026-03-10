<template>
  <div class="customers-container">
    <div class="customers-body">
      <lay-card>
        <template #body>
          <lay-field>
            <template #title>
              <span class="field-title">
                <lay-icon type="layui-icon-chart-screen" size="18px"></lay-icon>
                SAO KÊ GIAO DỊCH
              </span>
            </template>

            <lay-form :model="searchForm" class="search-form" mode="inline" label-width="auto">
              <lay-form-item>
                <lay-date-picker
                  v-model="searchForm.dateRange"
                  type="date"
                  range
                  single-panel
                  size="lg"
                  allow-clear
                  :placeholder="['Thời gian bắt đầu', 'Thời gian kết thúc']"
                ></lay-date-picker>
              </lay-form-item>
              <lay-form-item>
                <lay-select v-model="searchForm.quickDate" placeholder="Hôm nay" fit-content @change="onQuickDateChange">
                  <lay-select-option :value="quickDateValues.today" label="Hôm nay"></lay-select-option>
                  <lay-select-option :value="quickDateValues.yesterday" label="Hôm qua"></lay-select-option>
                  <lay-select-option :value="quickDateValues.thisWeek" label="Tuần này"></lay-select-option>
                  <lay-select-option :value="quickDateValues.thisMonth" label="Tháng này"></lay-select-option>
                  <lay-select-option :value="quickDateValues.lastMonth" label="Tháng trước"></lay-select-option>
                </lay-select>
              </lay-form-item>
              <lay-form-item label="Tên tài khoản：">
                <lay-input v-model="searchForm.username" placeholder="Nhập tên tài khoản" style="width: 200px"></lay-input>
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

          <lay-table :columns="columns" :data-source="tableData" :default-toolbar="['filter']" :page="pagination" @change="handlePageChange">
          </lay-table>

          <div class="summary-section">
            <span class="summary-title">Phương pháp tổng hợp [nhóm]:</span>
            <lay-table :columns="summaryColumns" :data-source="summaryData" even skin="nob">
            </lay-table>
          </div>
        </template>
      </lay-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

const now = new Date();
const today = formatDate(now);

const yesterday = new Date(now);
yesterday.setDate(yesterday.getDate() - 1);

const weekStart = new Date(now);
weekStart.setDate(weekStart.getDate() - weekStart.getDay() + 1);

const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1);
const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0);

const quickDateValues = {
  today: `${today} | ${today}`,
  yesterday: `${formatDate(yesterday)} | ${formatDate(yesterday)}`,
  thisWeek: `${formatDate(weekStart)} | ${today}`,
  thisMonth: `${formatDate(monthStart)} | ${today}`,
  lastMonth: `${formatDate(lastMonthStart)} | ${formatDate(lastMonthEnd)}`,
};

const searchForm = reactive({
  dateRange: [today, today] as string[],
  quickDate: quickDateValues.today,
  username: "",
});

function onQuickDateChange(val: string) {
  if (val) {
    const parts = val.split(" | ");
    searchForm.dateRange = [parts[0], parts[1]];
  }
}

const columns = ref([
  { title: "Tên tài khoản", key: "username", width: "150px" },
  { title: "Thuộc đại lý", key: "user_parent_format", width: "150px" },
  { title: "Số lần nạp", key: "deposit_count" },
  { title: "Số tiền nạp", key: "deposit_amount", minWidth: "150px", sort: true },
  { title: "Số lần rút", key: "withdrawal_count", minWidth: "150px" },
  { title: "Số tiền rút", key: "withdrawal_amount", minWidth: "160px" },
  { title: "Phí dịch vụ", key: "charge_fee", minWidth: "150px" },
  { title: "Hoa hồng đại lý", key: "agent_commission", minWidth: "150px" },
  { title: "Ưu đãi", key: "promotion", minWidth: "150px" },
  { title: "Hoàn trả bên thứ 3", key: "third_rebate", minWidth: "150px" },
  { title: "Tiền thưởng từ bên thứ 3", key: "third_activity_amount", minWidth: "150px" },
  { title: "Thời gian", key: "date", minWidth: "160px" },
]);

const tableData = ref([] as any[]);

const summaryColumns = ref([
  { title: "Số tiền nạp", key: "total_deposit_amount" },
  { title: "Số tiền rút", key: "total_withdrawal_amount" },
  { title: "Phí dịch vụ", key: "total_charge_fee" },
  { title: "Hoa hồng đại lý", key: "total_agent_commission" },
  { title: "Ưu đãi", key: "total_promotion" },
  { title: "Hoàn trả bên thứ 3", key: "total_third_rebate" },
  { title: "Tiền thưởng từ bên thứ 3", key: "total_third_activity_amount" },
]);

const summaryData = ref([
  {
    total_deposit_amount: "0.00",
    total_withdrawal_amount: "0.00",
    total_charge_fee: "0.00",
    total_agent_commission: "0.00",
    total_promotion: "0.00",
    total_third_rebate: "0.00",
    total_third_activity_amount: "0",
  },
]);

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
  searchForm.dateRange = [today, today];
  searchForm.quickDate = quickDateValues.today;
  searchForm.username = "";
}

function handlePageChange(page: any) {
  pagination.current = page.current;
  pagination.limit = page.limit;
}
</script>

<style scoped>
.customers-container {
  margin-top: 60px;
  min-height: calc(100vh - 60px);
  padding: 0;
  background: #f5f5f5;
}

.customers-body {
  margin: 10px 10px 0 10px;
}

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

.summary-section {
  margin-top: 10px;
  padding: 0;
}

.summary-title {
  font-weight: bold;
  display: block;
  margin-bottom: 6px;
}
</style>
