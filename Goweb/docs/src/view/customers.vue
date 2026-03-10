<template>
  <div class="customers-container">
    <div class="customers-body">
      <lay-card>
        <template #body>
          <lay-field>
            <template #title>
              <span class="field-title">
                <lay-icon type="layui-icon-group" size="18px"></lay-icon>
                QUẢN LÍ HỘI VIÊN THUỘC CẤP
              </span>
            </template>

            <lay-form :model="searchForm" class="search-form" mode="inline" label-width="auto">
              <lay-form-item label="Tên tài khoản：">
                <lay-input v-model="searchForm.username" placeholder="Nhập tên tài khoản"></lay-input>
              </lay-form-item>
              <lay-form-item label="Thời gian nạp đầu：">
                <lay-date-picker
                  v-model="searchForm.dateRange"
                  type="date"
                  range
                  single-panel
                  allow-clear
                  :placeholder="['Thời gian bắt đầu', 'Thời gian kết thúc']"
                ></lay-date-picker>
              </lay-form-item>
              <lay-form-item label="Trạng thái：">
                <lay-select v-model="searchForm.status" placeholder="Chọn" allow-clear fit-content>
                  <lay-select-option value="unrated" label="Chưa đánh giá"></lay-select-option>
                  <lay-select-option value="normal" label="Bình thường"></lay-select-option>
                  <lay-select-option value="frozen" label="Đóng băng"></lay-select-option>
                  <lay-select-option value="locked" label="Khoá"></lay-select-option>
                </lay-select>
              </lay-form-item>
              <lay-form-item label="Sắp xếp theo trường：">
                <lay-select v-model="searchForm.sortField" placeholder="Chọn" allow-clear fit-content>
                  <lay-select-option value="balance" label="Số dư"></lay-select-option>
                  <lay-select-option value="last_login" label="Lần đăng nhập cuối"></lay-select-option>
                  <lay-select-option value="created_at" label="Thời gian đăng ký"></lay-select-option>
                  <lay-select-option value="total_deposit" label="Tổng tiền nạp"></lay-select-option>
                  <lay-select-option value="total_withdraw" label="Tổng tiền rút"></lay-select-option>
                </lay-select>
              </lay-form-item>
              <lay-form-item label="Sắp xếp theo hướng：">
                <lay-select v-model="searchForm.sortDir" placeholder="Từ lớn đến bé" fit-content>
                  <lay-select-option value="desc" label="Từ lớn đến bé"></lay-select-option>
                  <lay-select-option value="asc" label="Từ bé đến lớn"></lay-select-option>
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

          <!-- Table với toolbar tích hợp -->
          <lay-table :columns="columns" :data-source="tableData" :default-toolbar="['filter', 'export', 'print']" :page="pagination" @change="handlePageChange">
            <template #toolbar>
              <lay-button-group>
                <lay-button type="primary" size="xs" @click="handleAddMember">
                  <lay-icon type="layui-icon-addition"></lay-icon> Thêm hội viên
                </lay-button>
                <lay-button type="primary" size="xs" @click="handleAddAgent">
                  <lay-icon type="layui-icon-addition"></lay-icon> Đại lý mới thêm
                </lay-button>
              </lay-button-group>
            </template>
            <template #status_format="{ row }">
              <lay-tag :type="statusTagType(row.status_format)">{{ row.status_format }}</lay-tag>
            </template>
            <template #operator="{ row }">
              <lay-button type="primary" size="xs" @click="handleRebate(row)">Cài đặt hoàn trả</lay-button>
            </template>
          </lay-table>
        </template>
      </lay-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useI18n } from "layui-component/index";

const { t } = useI18n();

const searchForm = reactive({
  username: "",
  dateRange: [] as string[],
  status: null as string | null,
  sortField: "" as string,
  sortDir: "desc",
});

const columns = ref([
  { title: "Hội viên", key: "username", width: "150px" },
  { title: "Loại hình hội viên", key: "type_format", width: "130px" },
  { title: "Tài khoản đại lý", key: "parent_user", width: "150px" },
  { title: "Số dư", key: "money", width: "120px" },
  { title: "Lần nạp", key: "deposit_count", width: "80px" },
  { title: "Lần rút", key: "withdrawal_count", width: "80px" },
  { title: "Tổng tiền nạp", key: "deposit_amount", width: "120px" },
  { title: "Tổng tiền rút", key: "withdrawal_amount", width: "120px" },
  { title: "Lần đăng nhập cuối", key: "login_time", width: "160px" },
  { title: "Thời gian đăng ký", key: "register_time", width: "160px" },
  { title: "Trạng thái", key: "status_format", width: "100px", customSlot: "status_format" },
  { title: "Thao tác", key: "operator", width: "130px", customSlot: "operator", fixed: "right" },
]);

const tableData = ref([
  {
    username: "an10tynghichoi",
    type_format: "Hội viên chính thức",
    parent_user: "vozer123",
    money: "0.0000",
    deposit_count: 0,
    withdrawal_count: 0,
    deposit_amount: "0.0000",
    withdrawal_amount: "0.0000",
    login_time: "",
    register_time: "2026-03-09 16:20:58",
    status_format: "Bình thường",
  },
]);

const pagination = reactive({
  current: 1,
  limit: 10,
  total: 1,
  limits: [10, 20, 30, 40, 50, 60, 70, 80, 90],
  layout: ["prev", "page", "next", "skip", "count", "limit"],
});

function statusTagType(status: string) {
  if (status === "Bình thường") return "normal";
  if (status === "Đóng băng") return "warm";
  if (status === "Khoá") return "danger";
  return "";
}

function handleSearch() {
  console.log("search", searchForm);
}

function handleReset() {
  searchForm.username = "";
  searchForm.dateRange = [];
  searchForm.status = null;
  searchForm.sortField = "";
  searchForm.sortDir = "desc";
}

function handlePageChange(page: any) {
  pagination.current = page.current;
  pagination.limit = page.limit;
}

function handleAddMember() {
  console.log("add member");
}

function handleAddAgent() {
  console.log("add agent");
}

function handleRebate(row: any) {
  console.log("rebate", row);
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

</style>
