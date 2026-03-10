<template>
  <PageLayout>
    <lay-field>
      <template #title>
        <span class="field-title">
          <lay-icon type="layui-icon-chart-screen" size="18px"></lay-icon>
          {{ t("transaction_log.title") }}
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
            :placeholder="[t('common.date_start'), t('common.date_end')]"
          ></lay-date-picker>
        </lay-form-item>
        <lay-form-item>
          <lay-select v-model="dateForm.quickDate" :placeholder="t('common.today')" fit-content @change="onQuickDateChange">
            <lay-select-option :value="quickDateValues.today" :label="t('common.today')"></lay-select-option>
            <lay-select-option :value="quickDateValues.yesterday" :label="t('common.yesterday')"></lay-select-option>
            <lay-select-option :value="quickDateValues.thisWeek" :label="t('common.this_week')"></lay-select-option>
            <lay-select-option :value="quickDateValues.thisMonth" :label="t('common.this_month')"></lay-select-option>
            <lay-select-option :value="quickDateValues.lastMonth" :label="t('common.last_month')"></lay-select-option>
          </lay-select>
        </lay-form-item>
        <lay-form-item :label="t('common.username_label')">
          <lay-input v-model="searchForm.username" :placeholder="t('common.username_placeholder')" style="width: 200px"></lay-input>
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

    <lay-table :columns="columns" :data-source="tableData" :default-toolbar="['filter', 'export', 'print']" :page="pagination" @change="handlePageChange">
    </lay-table>

    <div class="summary-section">
      <span class="summary-title">{{ t("common.summary_group") }}</span>
      <lay-table :columns="summaryColumns" :data-source="summaryData" even skin="nob">
      </lay-table>
    </div>
  </PageLayout>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from "vue";
import { useI18n } from "layui-component/index";
import PageLayout from "../../components/PageLayout.vue";
import { useQuickDate } from "../../composables/useQuickDate";

const { t } = useI18n();
const { quickDateValues, dateForm, onQuickDateChange, resetDate } = useQuickDate();

const searchForm = reactive({
  username: "",
});

const columns = computed(() => [
  { title: t("transaction_log.col_username"), key: "username", width: "150px" },
  { title: t("transaction_log.col_agent"), key: "user_parent_format", width: "150px" },
  { title: t("transaction_log.col_deposit_count"), key: "deposit_count" },
  { title: t("transaction_log.col_deposit_amount"), key: "deposit_amount", minWidth: "150px" },
  { title: t("transaction_log.col_withdraw_count"), key: "withdrawal_count", minWidth: "150px" },
  { title: t("transaction_log.col_withdraw_amount"), key: "withdrawal_amount", minWidth: "160px" },
  { title: t("transaction_log.col_service_fee"), key: "charge_fee", minWidth: "150px" },
  { title: t("transaction_log.col_agent_commission"), key: "agent_commission", minWidth: "150px" },
  { title: t("transaction_log.col_promotion"), key: "promotion", minWidth: "150px" },
  { title: t("transaction_log.col_third_party_rebate"), key: "third_rebate", minWidth: "150px" },
  { title: t("transaction_log.col_third_party_bonus"), key: "third_activity_amount", minWidth: "150px" },
  { title: t("transaction_log.col_time"), key: "date", minWidth: "160px" },
]);

const tableData = ref([] as any[]);

const summaryColumns = computed(() => [
  { title: t("transaction_log.sum_deposit_amount"), key: "total_deposit_amount" },
  { title: t("transaction_log.sum_withdraw_amount"), key: "total_withdrawal_amount" },
  { title: t("transaction_log.sum_service_fee"), key: "total_charge_fee" },
  { title: t("transaction_log.sum_agent_commission"), key: "total_agent_commission" },
  { title: t("transaction_log.sum_promotion"), key: "total_promotion" },
  { title: t("transaction_log.sum_third_party_rebate"), key: "total_third_rebate" },
  { title: t("transaction_log.sum_third_party_bonus"), key: "total_third_activity_amount" },
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

function handlePageChange(page: any) {
  pagination.current = page.current;
  pagination.limit = page.limit;
}

function handleSearch() {
  console.log("search", { ...dateForm, ...searchForm });
}

function handleReset() {
  resetDate();
  searchForm.username = "";
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
