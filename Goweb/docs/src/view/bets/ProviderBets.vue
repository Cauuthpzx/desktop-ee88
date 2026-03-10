<template>
  <PageLayout>
    <lay-field>
      <template #title>
        <span class="field-title">
          <lay-icon type="layui-icon-form" size="18px"></lay-icon>
          ĐƠN CƯỢC BÊN THỨ 3
        </span>
      </template>

      <lay-form :model="searchForm" class="search-form" mode="inline" label-width="auto">
        <lay-form-item label="Thời gian cược：">
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
            <lay-select-option :value="quickDateValues.thisWeek" label="Tuần này"></lay-select-option>
            <lay-select-option :value="quickDateValues.thisMonth" label="Tháng này"></lay-select-option>
            <lay-select-option :value="quickDateValues.lastMonth" label="Tháng trước"></lay-select-option>
          </lay-select>
        </lay-form-item>
        <lay-form-item label="Mã giao dịch：">
          <lay-input v-model="searchForm.serialNo" placeholder="Nhập hoàn chỉnh đơn giao dịch" style="width: 200px"></lay-input>
        </lay-form-item>
        <lay-form-item label="Tên tài khoản thuộc nhà cái：">
          <lay-input v-model="searchForm.platformUsername" placeholder="Nhập tên tài khoản thuộc nhà cái" style="width: 200px"></lay-input>
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
import { useQuickDate } from "../../composables/useQuickDate";

const { quickDateValues, dateForm, onQuickDateChange, resetDate } = useQuickDate();

const searchForm = reactive({
  serialNo: "",
  platformUsername: "",
});

const columns = ref([
  { title: "Mã giao dịch", key: "serial_no", width: "250px" },
  { title: "Nhà cung cấp game bên thứ 3", key: "platform_id_name", minWidth: "150px" },
  { title: "Tên tài khoản thuộc nhà cái", key: "platform_username", minWidth: "150px" },
  { title: "Loại hình trò chơi", key: "c_name", minWidth: "150px" },
  { title: "Tên trò chơi bên thứ 3", key: "game_name", minWidth: "150px" },
  { title: "Tiền cược", key: "bet_amount", minWidth: "150px" },
  { title: "Tiền cược hợp lệ", key: "turnover", minWidth: "150px" },
  { title: "Tiền thưởng", key: "prize", minWidth: "150px" },
  { title: "Thắng thua", key: "win_lose", minWidth: "150px" },
  { title: "Thời gian cược", key: "bet_time", minWidth: "160px" },
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
  console.log("search", { ...dateForm, ...searchForm });
}

function handleReset() {
  resetDate();
  searchForm.serialNo = "";
  searchForm.platformUsername = "";
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
