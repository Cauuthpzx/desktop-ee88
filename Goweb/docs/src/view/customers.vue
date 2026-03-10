<template>
  <div class="customers-container">
    <div class="customers-body">
      <lay-card>
        <template #body>
          <lay-field>
            <template #title>
              <span class="field-title">
                <lay-icon type="layui-icon-group" size="18px"></lay-icon>
                {{ t("customers.title") }}
              </span>
            </template>

            <lay-form :model="searchForm" class="search-form" mode="inline" label-width="auto">
              <lay-form-item :label="t('common.username_label')">
                <lay-input v-model="searchForm.username" :placeholder="t('common.username_placeholder')"></lay-input>
              </lay-form-item>
              <lay-form-item :label="t('customers.first_deposit_date')">
                <lay-date-picker
                  v-model="searchForm.dateRange"
                  type="date"
                  range
                  single-panel
                  allow-clear
                  :placeholder="[t('common.date_start'), t('common.date_end')]"
                ></lay-date-picker>
              </lay-form-item>
              <lay-form-item :label="t('customers.status_label')">
                <lay-select v-model="searchForm.status" :placeholder="t('common.select')" allow-clear fit-content>
                  <lay-select-option value="unrated" :label="t('customers.status_unrated')"></lay-select-option>
                  <lay-select-option value="normal" :label="t('customers.status_normal')"></lay-select-option>
                  <lay-select-option value="frozen" :label="t('customers.status_frozen')"></lay-select-option>
                  <lay-select-option value="locked" :label="t('customers.status_locked')"></lay-select-option>
                </lay-select>
              </lay-form-item>
              <lay-form-item :label="t('customers.sort_field_label')">
                <lay-select v-model="searchForm.sortField" :placeholder="t('common.select')" allow-clear fit-content>
                  <lay-select-option value="balance" :label="t('customers.sort_balance')"></lay-select-option>
                  <lay-select-option value="last_login" :label="t('customers.sort_last_login')"></lay-select-option>
                  <lay-select-option value="created_at" :label="t('customers.sort_created_at')"></lay-select-option>
                  <lay-select-option value="total_deposit" :label="t('customers.sort_total_deposit')"></lay-select-option>
                  <lay-select-option value="total_withdraw" :label="t('customers.sort_total_withdraw')"></lay-select-option>
                </lay-select>
              </lay-form-item>
              <lay-form-item :label="t('customers.sort_dir_label')">
                <lay-select v-model="searchForm.sortDir" :placeholder="t('customers.sort_desc')" fit-content>
                  <lay-select-option value="desc" :label="t('customers.sort_desc')"></lay-select-option>
                  <lay-select-option value="asc" :label="t('customers.sort_asc')"></lay-select-option>
                </lay-select>
              </lay-form-item>
              <lay-form-item>
                <lay-button type="primary" @click="handleSearch">
                  <lay-icon type="layui-icon-search"></lay-icon> {{ t("common.search") }}
                </lay-button>
                <lay-button @click="handleReset">
                  <lay-icon type="layui-icon-refresh"></lay-icon> {{ t("common.reset") }}
                </lay-button>
              </lay-form-item>
            </lay-form>
          </lay-field>

          <!-- Table với toolbar tích hợp -->
          <lay-table :columns="columns" :data-source="tableData" :default-toolbar="['filter', 'export', 'print']" :page="pagination" @change="handlePageChange">
            <template #toolbar>
              <lay-button-group>
                <lay-button type="primary" size="xs" @click="handleAddMember">
                  <lay-icon type="layui-icon-addition"></lay-icon> {{ t("customers.add_member") }}
                </lay-button>
                <lay-button type="primary" size="xs" @click="handleAddAgent">
                  <lay-icon type="layui-icon-addition"></lay-icon> {{ t("customers.add_agent") }}
                </lay-button>
              </lay-button-group>
            </template>
            <template #status_format="{ row }">
              <lay-tag :type="statusTagType(row.status_format)">{{ row.status_format }}</lay-tag>
            </template>
            <template #operator="{ row }">
              <lay-button type="primary" size="xs" @click="handleRebate(row)">{{ t("customers.rebate_settings") }}</lay-button>
            </template>
          </lay-table>
        </template>
      </lay-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from "vue";
import { useI18n } from "layui-component/index";

const { t } = useI18n();

const searchForm = reactive({
  username: "",
  dateRange: [] as string[],
  status: null as string | null,
  sortField: "" as string,
  sortDir: "desc",
});

const columns = computed(() => [
  { title: t("customers.col_member"), key: "username", width: "150px" },
  { title: t("customers.col_member_type"), key: "type_format", width: "130px" },
  { title: t("customers.col_agent_account"), key: "parent_user", width: "150px" },
  { title: t("customers.col_balance"), key: "money", width: "120px" },
  { title: t("customers.col_deposit_count"), key: "deposit_count", width: "80px" },
  { title: t("customers.col_withdraw_count"), key: "withdrawal_count", width: "80px" },
  { title: t("customers.col_total_deposit"), key: "deposit_amount", width: "120px" },
  { title: t("customers.col_total_withdraw"), key: "withdrawal_amount", width: "120px" },
  { title: t("customers.col_last_login"), key: "login_time", width: "160px" },
  { title: t("customers.col_register_time"), key: "register_time", width: "160px" },
  { title: t("customers.col_status"), key: "status_format", width: "100px", customSlot: "status_format" },
  { title: t("customers.col_action"), key: "operator", width: "130px", customSlot: "operator", fixed: "right" },
]);

const tableData = ref([
  {
    username: "an10tynghichoi",
    type_format: t("customers.type_official"),
    parent_user: "vozer123",
    money: "0.0000",
    deposit_count: 0,
    withdrawal_count: 0,
    deposit_amount: "0.0000",
    withdrawal_amount: "0.0000",
    login_time: "",
    register_time: "2026-03-09 16:20:58",
    status_format: t("customers.status_normal"),
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
  if (status === t("customers.status_normal")) return "normal";
  if (status === t("customers.status_frozen")) return "warm";
  if (status === t("customers.status_locked")) return "danger";
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
