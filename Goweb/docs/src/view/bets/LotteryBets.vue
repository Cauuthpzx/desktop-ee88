<template>
  <PageLayout>
    <lay-field>
      <template #title>
        <span class="field-title">
          <lay-icon type="layui-icon-form" size="18px"></lay-icon>
          DANH SÁCH ĐƠN CƯỢC
        </span>
      </template>

      <lay-form :model="searchForm" class="search-form" mode="inline" label-width="auto">
        <lay-form-item>
          <lay-date-picker
            v-model="dateForm.dateRange"
            type="date"
            range
            single-panel
            allow-clear
            :placeholder="['Thời gian bắt đầu', 'Thời gian kết thúc']"
          ></lay-date-picker>
        </lay-form-item>
        <lay-form-item>
          <lay-select v-model="dateForm.quickDate" placeholder="Hôm nay" fit-content @change="onQuickDateChange">
            <lay-select-option :value="quickDateValues.today" label="Hôm nay"></lay-select-option>
            <lay-select-option :value="quickDateValues.yesterday" label="Hôm qua"></lay-select-option>
          </lay-select>
        </lay-form-item>
        <lay-form-item label="Tên người dùng：">
          <lay-input v-model="searchForm.username" placeholder="Vui lòng nhập đầy đủ Tên người dùng" style="width: 200px"></lay-input>
        </lay-form-item>
        <lay-form-item label="Mã giao dịch：">
          <lay-input v-model="searchForm.serialNo" placeholder="Nhập đầy đủ mã giao dịch" style="width: 200px"></lay-input>
        </lay-form-item>
        <lay-form-item label="Trò chơi：">
          <lay-select v-model="searchForm.lotteryId" placeholder="Chọn" allow-clear searchable style="width: 150px">
            <lay-select-option value="67" label="Sicbo 30 giây"></lay-select-option>
            <lay-select-option value="66" label="Sicbo 20 giây"></lay-select-option>
            <lay-select-option value="68" label="Sicbo 40 giây"></lay-select-option>
            <lay-select-option value="69" label="Sicbo 50 giây"></lay-select-option>
            <lay-select-option value="70" label="Sicbo 1 phút"></lay-select-option>
            <lay-select-option value="71" label="Sicbo 1.5 phút"></lay-select-option>
            <lay-select-option value="32" label="Miền Bắc"></lay-select-option>
            <lay-select-option value="63" label="Xổ số Miền Bắc"></lay-select-option>
            <lay-select-option value="47" label="Miền Bắc VIP 45 giây"></lay-select-option>
            <lay-select-option value="48" label="Miền Bắc VIP 75 giây"></lay-select-option>
            <lay-select-option value="49" label="Miền Bắc VIP 2 phút"></lay-select-option>
            <lay-select-option value="45" label="MB siêu tốc 5 phút"></lay-select-option>
            <lay-select-option value="46" label="MB siêu tốc 3 phút"></lay-select-option>
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
            <lay-select-option value="51" label="Keno VIP 20 giây"></lay-select-option>
            <lay-select-option value="52" label="Keno VIP 30 giây"></lay-select-option>
            <lay-select-option value="53" label="Keno VIP 40 giây"></lay-select-option>
            <lay-select-option value="54" label="Keno VIP 50 giây"></lay-select-option>
            <lay-select-option value="55" label="Keno VIP 1 phút"></lay-select-option>
            <lay-select-option value="56" label="Keno VIP 5 phút"></lay-select-option>
            <lay-select-option value="77" label="Win go 30 giây"></lay-select-option>
            <lay-select-option value="73" label="Win go 45 giây"></lay-select-option>
            <lay-select-option value="74" label="Win go 1 phút"></lay-select-option>
            <lay-select-option value="75" label="Win go 3 phút"></lay-select-option>
            <lay-select-option value="76" label="Win go 5 phút"></lay-select-option>
            <lay-select-option value="72" label="Oẳn tù tì"></lay-select-option>
          </lay-select>
        </lay-form-item>
        <lay-form-item label="Loại trò chơi：">
          <lay-select v-model="searchForm.playTypeId" placeholder="Chọn" allow-clear searchable style="width: 180px">
          </lay-select>
        </lay-form-item>
        <lay-form-item label="Cách chơi：">
          <lay-select v-model="searchForm.playId" placeholder="Chọn" allow-clear searchable style="width: 180px">
          </lay-select>
        </lay-form-item>
        <lay-form-item label="Trạng thái：">
          <lay-select v-model="searchForm.status" placeholder="Chọn" allow-clear searchable style="width: 150px">
            <lay-select-option value="-9" label="Chưa thanh toán"></lay-select-option>
            <lay-select-option value="1" label="Trúng"></lay-select-option>
            <lay-select-option value="-1" label="Không trúng"></lay-select-option>
            <lay-select-option value="2" label="Hoà"></lay-select-option>
            <lay-select-option value="3" label="Khách huỷ đơn"></lay-select-option>
            <lay-select-option value="4" label="Hệ thống huỷ đơn"></lay-select-option>
            <lay-select-option value="5" label="Đơn cược bất thường"></lay-select-option>
            <lay-select-option value="6" label="Chưa thanh toán (khôi phục thủ công)"></lay-select-option>
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

    <div class="summary-section">
      <span class="summary-title">Dữ liệu tổng hợp:</span>
      <lay-table :columns="summaryColumns" :data-source="summaryData" even skin="nob">
      </lay-table>
    </div>
  </PageLayout>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import PageLayout from "../../components/PageLayout.vue";
import { useQuickDate } from "../../composables/useQuickDate";

const { quickDateValues, dateForm, onQuickDateChange, resetDate } = useQuickDate({ onlyTodayYesterday: true });

const searchForm = reactive({
  username: "",
  serialNo: "",
  lotteryId: null as string | null,
  playTypeId: null as string | null,
  playId: null as string | null,
  status: null as string | null,
});

const columns = ref([
  { title: "Mã giao dịch", key: "serial_no", width: "200px" },
  { title: "Tên người dùng", key: "username", width: "150px" },
  { title: "Thời gian cược", key: "create_time", width: "160px" },
  { title: "Trò chơi", key: "lottery_name", minWidth: "150px" },
  { title: "Loại trò chơi", key: "play_type_name", minWidth: "150px" },
  { title: "Cách chơi", key: "play_name", minWidth: "150px" },
  { title: "Kỳ", key: "issue", minWidth: "150px" },
  { title: "Thông tin cược", key: "content", minWidth: "150px" },
  { title: "Tiền cược", key: "money", minWidth: "150px" },
  { title: "Tiền hoàn trả", key: "rebate_amount", minWidth: "150px" },
  { title: "Thắng thua", key: "result", minWidth: "150px" },
  { title: "Trạng thái", key: "status_text", width: "100px" },
]);

const tableData = ref([] as any[]);

const summaryColumns = ref([
  { title: "Tiền cược", key: "total_money" },
  { title: "Tiền hoàn trả", key: "total_rebate_amount" },
  { title: "Thắng thua", key: "total_result" },
]);

const summaryData = ref([
  {
    total_money: "0.00",
    total_rebate_amount: "0.00",
    total_result: "0.00",
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
  console.log("search", { ...dateForm, ...searchForm });
}

function handleReset() {
  resetDate();
  searchForm.username = "";
  searchForm.serialNo = "";
  searchForm.lotteryId = null;
  searchForm.playTypeId = null;
  searchForm.playId = null;
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
