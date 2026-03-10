<template>
  <div class="customers-container">
    <div class="customers-body">
      <lay-card>
        <template #body>
          <lay-field>
            <template #title>
              <span class="field-title">
                <lay-icon type="layui-icon-chart-screen" size="18px"></lay-icon>
                BÁO CÁO NHÀ CUNG CẤP
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
              <lay-form-item label="Nhà cung cấp game：">
                <lay-select v-model="searchForm.platformId" placeholder="Chọn" allow-clear searchable style="width: 200px">
                  <lay-select-option value="8" label="PA"></lay-select-option>
                  <lay-select-option value="9" label="BBIN"></lay-select-option>
                  <lay-select-option value="10" label="WM"></lay-select-option>
                  <lay-select-option value="14" label="MINI"></lay-select-option>
                  <lay-select-option value="20" label="KY"></lay-select-option>
                  <lay-select-option value="28" label="PGSOFT"></lay-select-option>
                  <lay-select-option value="29" label="LUCKYWIN"></lay-select-option>
                  <lay-select-option value="30" label="SABA"></lay-select-option>
                  <lay-select-option value="31" label="PT"></lay-select-option>
                  <lay-select-option value="38" label="RICH88"></lay-select-option>
                  <lay-select-option value="43" label="ASTAR"></lay-select-option>
                  <lay-select-option value="45" label="FB"></lay-select-option>
                  <lay-select-option value="46" label="JILI"></lay-select-option>
                  <lay-select-option value="47" label="KA"></lay-select-option>
                  <lay-select-option value="48" label="MW"></lay-select-option>
                  <lay-select-option value="50" label="SBO"></lay-select-option>
                  <lay-select-option value="51" label="NEXTSPIN"></lay-select-option>
                  <lay-select-option value="52" label="AMB"></lay-select-option>
                  <lay-select-option value="53" label="FunTa"></lay-select-option>
                  <lay-select-option value="62" label="MG"></lay-select-option>
                  <lay-select-option value="63" label="WS168"></lay-select-option>
                  <lay-select-option value="69" label="DG CASINO"></lay-select-option>
                  <lay-select-option value="70" label="V8"></lay-select-option>
                  <lay-select-option value="71" label="AE"></lay-select-option>
                  <lay-select-option value="72" label="TP"></lay-select-option>
                  <lay-select-option value="73" label="FC"></lay-select-option>
                  <lay-select-option value="74" label="JDB"></lay-select-option>
                  <lay-select-option value="75" label="CQ9"></lay-select-option>
                  <lay-select-option value="76" label="PP"></lay-select-option>
                  <lay-select-option value="77" label="VA"></lay-select-option>
                  <lay-select-option value="78" label="BNG"></lay-select-option>
                  <lay-select-option value="84" label="DB CASINO"></lay-select-option>
                  <lay-select-option value="85" label="EVO CASINO"></lay-select-option>
                  <lay-select-option value="90" label="CMD SPORTS"></lay-select-option>
                  <lay-select-option value="91" label="PG NEW"></lay-select-option>
                  <lay-select-option value="92" label="FBLIVE"></lay-select-option>
                  <lay-select-option value="93" label="ON CASINO"></lay-select-option>
                  <lay-select-option value="94" label="MT"></lay-select-option>
                  <lay-select-option value="101" label="JILI NEW"></lay-select-option>
                  <lay-select-option value="102" label="fC NEW"></lay-select-option>
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

          <lay-table :columns="columns" :data-source="tableData" :default-toolbar="['filter']" :page="pagination" @change="handlePageChange">
          </lay-table>

          <div class="summary-section">
            <span class="summary-title">Dữ liệu tổng hợp:</span>
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
  platformId: null as string | null,
});

function onQuickDateChange(val: string) {
  if (val) {
    const parts = val.split(" | ");
    searchForm.dateRange = [parts[0], parts[1]];
  }
}

const columns = ref([
  { title: "Tên tài khoản", key: "username" },
  { title: "Nhà cung cấp game", key: "platform_id_name" },
  { title: "Số lần cược", key: "t_bet_times" },
  { title: "Tiền cược", key: "t_bet_amount" },
  { title: "Tiền cược hợp lệ", key: "t_turnover" },
  { title: "Tiền thưởng", key: "t_prize" },
  { title: "Thắng thua", key: "t_win_lose" },
]);

const tableData = ref([] as any[]);

const summaryColumns = ref([
  { title: "Số lần cược", key: "total_bet_times" },
  { title: "Số khách đặt cược", key: "total_bet_number" },
  { title: "Tiền cược", key: "total_bet_amount" },
  { title: "Tiền cược hợp lệ", key: "total_turnover" },
  { title: "Tiền thưởng", key: "total_prize" },
  { title: "Thắng thua", key: "total_win_lose" },
]);

const summaryData = ref([
  {
    total_bet_times: 0,
    total_bet_number: 0,
    total_bet_amount: "0.00",
    total_turnover: "0.00",
    total_prize: "0.00",
    total_win_lose: "0.00",
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
  searchForm.platformId = null;
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
