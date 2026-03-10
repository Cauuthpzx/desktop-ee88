<template>
  <div class="customers-container">
    <div class="customers-body">
      <lay-card>
        <template #body>
          <lay-field>
            <template #title>
              <span class="field-title">
                <lay-icon type="layui-icon-chart-screen" size="18px"></lay-icon>
                BÁO CÁO XỔ SỐ
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
              <lay-form-item label="Tên loại xổ：">
                <lay-select v-model="searchForm.lotteryId" placeholder="Chọn hoặc nhập để tìm kiếm" allow-clear searchable style="width: 200px">
                  <lay-select-option-group label="Sicbo">
                    <lay-select-option value="67" label="Sicbo 30 giây"></lay-select-option>
                    <lay-select-option value="66" label="Sicbo 20 giây"></lay-select-option>
                    <lay-select-option value="68" label="Sicbo 40 giây"></lay-select-option>
                    <lay-select-option value="69" label="Sicbo 50 giây"></lay-select-option>
                    <lay-select-option value="70" label="Sicbo 1 phút"></lay-select-option>
                    <lay-select-option value="71" label="Sicbo 1.5 phút"></lay-select-option>
                  </lay-select-option-group>
                  <lay-select-option-group label="Miền Bắc">
                    <lay-select-option value="32" label="Miền Bắc"></lay-select-option>
                    <lay-select-option value="63" label="Xổ số Miền Bắc"></lay-select-option>
                    <lay-select-option value="47" label="Miền Bắc VIP 45 giây"></lay-select-option>
                    <lay-select-option value="48" label="Miền Bắc VIP 75 giây"></lay-select-option>
                    <lay-select-option value="49" label="Miền Bắc VIP 2 phút"></lay-select-option>
                    <lay-select-option value="45" label="MB siêu tốc 5 phút"></lay-select-option>
                    <lay-select-option value="46" label="MB siêu tốc 3 phút"></lay-select-option>
                  </lay-select-option-group>
                  <lay-select-option-group label="Miền Trung">
                    <lay-select-option value="28" label="Gia Lai"></lay-select-option>
                    <lay-select-option value="29" label="Bình Định"></lay-select-option>
                    <lay-select-option value="30" label="Đắk Lắk"></lay-select-option>
                    <lay-select-option value="31" label="Đắk Nông"></lay-select-option>
                    <lay-select-option value="27" label="Khánh Hoà"></lay-select-option>
                    <lay-select-option value="26" label="Kon Tum"></lay-select-option>
                    <lay-select-option value="25" label="Ninh Thuận"></lay-select-option>
                    <lay-select-option value="24" label="Quảng Ngãi"></lay-select-option>
                    <lay-select-option value="23" label="Quảng Nam"></lay-select-option>
                    <lay-select-option value="22" label="Quảng Bình"></lay-select-option>
                    <lay-select-option value="21" label="Phú Yên"></lay-select-option>
                    <lay-select-option value="20" label="Quảng Trị"></lay-select-option>
                    <lay-select-option value="19" label="Thừa Thiên Huế"></lay-select-option>
                    <lay-select-option value="18" label="Đà Nẵng"></lay-select-option>
                  </lay-select-option-group>
                  <lay-select-option-group label="Miền Nam">
                    <lay-select-option value="1" label="Bạc Liêu"></lay-select-option>
                    <lay-select-option value="2" label="Vũng Tàu"></lay-select-option>
                    <lay-select-option value="3" label="Tiền Giang"></lay-select-option>
                    <lay-select-option value="4" label="Kiên Giang"></lay-select-option>
                    <lay-select-option value="5" label="Đà Lạt"></lay-select-option>
                    <lay-select-option value="6" label="Bình Phước"></lay-select-option>
                    <lay-select-option value="7" label="Bình Dương"></lay-select-option>
                    <lay-select-option value="8" label="An Giang"></lay-select-option>
                    <lay-select-option value="9" label="Bình Thuận"></lay-select-option>
                    <lay-select-option value="10" label="Cà Mau"></lay-select-option>
                    <lay-select-option value="11" label="Cần Thơ"></lay-select-option>
                    <lay-select-option value="12" label="Hậu Giang"></lay-select-option>
                    <lay-select-option value="13" label="Đồng Tháp"></lay-select-option>
                    <lay-select-option value="14" label="Tây Ninh"></lay-select-option>
                    <lay-select-option value="15" label="Sóc Trăng"></lay-select-option>
                    <lay-select-option value="16" label="TP Hồ Chí Minh"></lay-select-option>
                    <lay-select-option value="17" label="Đồng Nai"></lay-select-option>
                    <lay-select-option value="42" label="Trà Vinh"></lay-select-option>
                    <lay-select-option value="43" label="Vĩnh Long"></lay-select-option>
                    <lay-select-option value="61" label="Bến Tre"></lay-select-option>
                    <lay-select-option value="62" label="Long An"></lay-select-option>
                    <lay-select-option value="57" label="Miền Nam VIP 45 giây"></lay-select-option>
                    <lay-select-option value="44" label="Miền Nam VIP 5 phút"></lay-select-option>
                    <lay-select-option value="60" label="Miền Nam VIP 2 phút"></lay-select-option>
                    <lay-select-option value="59" label="Miền Nam VIP 90 giây"></lay-select-option>
                    <lay-select-option value="58" label="Miền Nam VIP 1 phút"></lay-select-option>
                  </lay-select-option-group>
                  <lay-select-option-group label="Keno VIP">
                    <lay-select-option value="51" label="Keno VIP 20 giây"></lay-select-option>
                    <lay-select-option value="52" label="Keno VIP 30 giây"></lay-select-option>
                    <lay-select-option value="53" label="Keno VIP 40 giây"></lay-select-option>
                    <lay-select-option value="54" label="Keno VIP 50 giây"></lay-select-option>
                    <lay-select-option value="55" label="Keno VIP 1 phút"></lay-select-option>
                    <lay-select-option value="56" label="Keno VIP 5 phút"></lay-select-option>
                  </lay-select-option-group>
                  <lay-select-option-group label="Win Go">
                    <lay-select-option value="77" label="Win go 30 giây"></lay-select-option>
                    <lay-select-option value="73" label="Win go 45 giây"></lay-select-option>
                    <lay-select-option value="74" label="Win go 1 phút"></lay-select-option>
                    <lay-select-option value="75" label="Win go 3 phút"></lay-select-option>
                    <lay-select-option value="76" label="Win go 5 phút"></lay-select-option>
                  </lay-select-option-group>
                  <lay-select-option-group label="Khác">
                    <lay-select-option value="72" label="Oẳn tù tì"></lay-select-option>
                  </lay-select-option-group>
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
  lotteryId: null as string | null,
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
  { title: "Số lần cược", key: "bet_count", minWidth: "150px" },
  { title: "Tiền cược", key: "bet_amount", minWidth: "150px" },
  { title: "Tiền cược hợp lệ (trừ cược hoà)", key: "valid_amount", minWidth: "160px" },
  { title: "Hoàn trả", key: "rebate_amount", minWidth: "150px" },
  { title: "Thắng thua", key: "result", minWidth: "150px" },
  { title: "Kết quả thắng thua (không gồm hoàn trả)", key: "win_lose", minWidth: "180px" },
  { title: "Tiền trúng", key: "prize", minWidth: "150px" },
  { title: "Tên loại xổ", key: "lottery_name", width: "160px" },
]);

const tableData = ref([] as any[]);

const summaryColumns = ref([
  { title: "Số khách đặt cược", key: "total_bet_number" },
  { title: "Số lần cược", key: "total_bet_count" },
  { title: "Tiền cược", key: "total_bet_amount" },
  { title: "Tiền cược hợp lệ (trừ cược hoà)", key: "total_valid_amount" },
  { title: "Hoàn trả", key: "total_rebate_amount" },
  { title: "Thắng thua", key: "total_result" },
  { title: "Kết quả thắng thua (không gồm hoàn trả)", key: "total_win_lose" },
  { title: "Tiền trúng", key: "total_prize" },
]);

const summaryData = ref([
  {
    total_bet_number: 0,
    total_bet_count: 0,
    total_bet_amount: "0.00",
    total_valid_amount: "0.00",
    total_rebate_amount: "0.00",
    total_result: "0.00",
    total_win_lose: "0.00",
    total_prize: "0.00",
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
  searchForm.lotteryId = null;
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
