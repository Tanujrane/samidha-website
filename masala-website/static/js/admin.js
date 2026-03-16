document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.querySelector(".admin-sidebar");
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const deleteForms = document.querySelectorAll("[data-confirm-delete]");
    const dashboardConfig = window.adminDashboardData;

    if (toggle && sidebar) {
        toggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
    }

    deleteForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            const confirmed = window.confirm("Delete this record permanently?");

            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    if (!dashboardConfig || typeof Chart === "undefined") {
        return;
    }

    const metricElements = {
        total_orders: document.querySelector("[data-metric='total_orders']"),
        total_revenue: document.querySelector("[data-metric='total_revenue']"),
        total_products: document.querySelector("[data-metric='total_products']"),
        processing_orders: document.querySelector("[data-metric='processing_orders']"),
        todays_sales: document.querySelector("[data-metric='todays_sales']"),
    };
    const salesChartElement = document.getElementById("salesChart");
    const topProductsChartElement = document.getElementById("topProductsChart");
    const recentOrdersBody = document.querySelector("[data-recent-orders-body]");
    const ordersTableWrap = document.querySelector("[data-orders-table-wrap]");
    const ordersEmptyState = document.querySelector("[data-orders-empty-state]");
    const liveIndicator = document.querySelector("[data-live-indicator]");

    const formatCurrency = (value) => `Rs. ${Math.round(Number(value) || 0)}`;
    const escapeHtml = (value) =>
        String(value ?? "").replace(/[&<>"']/g, (char) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }[char]));

    const salesChart = new Chart(salesChartElement, {
        type: "line",
        data: {
            labels: dashboardConfig.metrics.sales_labels,
            datasets: [{
                label: "Revenue",
                data: dashboardConfig.metrics.sales_values,
                borderColor: "#8B1E1E",
                backgroundColor: "rgba(230, 164, 0, 0.18)",
                fill: true,
                tension: 0.32,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: dashboardConfig.metrics.has_order_data },
            },
        },
    });

    const topProductsChart = new Chart(topProductsChartElement, {
        type: "bar",
        data: {
            labels: dashboardConfig.metrics.top_labels,
            datasets: [{
                label: "Units",
                data: dashboardConfig.metrics.top_values,
                backgroundColor: ["#8B1E1E", "#A44B2B", "#E6A400", "#6B3E2E", "#C46F1B"],
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: dashboardConfig.metrics.top_values.length > 0 },
            },
        },
    });

    const renderRecentOrders = (orders) => {
        if (!recentOrdersBody || !ordersTableWrap || !ordersEmptyState) {
            return;
        }

        if (!orders.length) {
            recentOrdersBody.innerHTML = "";
            ordersTableWrap.classList.add("is-hidden");
            ordersEmptyState.classList.remove("is-hidden");
            return;
        }

        recentOrdersBody.innerHTML = orders.map((order) => `
            <tr>
                <td>#${escapeHtml(order.id)}</td>
                <td>${escapeHtml(order.customer_name)}</td>
                <td>${escapeHtml(order.items)}</td>
                <td>${formatCurrency(order.total_price)}</td>
                <td>${escapeHtml(order.date)}</td>
                <td><span class="status-pill">${escapeHtml(order.status)}</span></td>
            </tr>
        `).join("");
        ordersTableWrap.classList.remove("is-hidden");
        ordersEmptyState.classList.add("is-hidden");
    };

    const updateMetrics = (metrics) => {
        metricElements.total_orders.textContent = metrics.total_orders;
        metricElements.total_revenue.textContent = formatCurrency(metrics.total_revenue);
        metricElements.total_products.textContent = metrics.total_products;
        metricElements.processing_orders.textContent = metrics.processing_orders;
        metricElements.todays_sales.textContent = formatCurrency(metrics.todays_sales);

        salesChart.data.labels = metrics.sales_labels;
        salesChart.data.datasets[0].data = metrics.sales_values;
        salesChart.options.plugins.tooltip.enabled = metrics.has_order_data;
        salesChart.update();

        topProductsChart.data.labels = metrics.top_labels;
        topProductsChart.data.datasets[0].data = metrics.top_values;
        topProductsChart.options.plugins.tooltip.enabled = metrics.top_values.length > 0;
        topProductsChart.update();
    };

    const setIndicatorState = (statusText, isError = false) => {
        if (!liveIndicator) {
            return;
        }
        liveIndicator.textContent = statusText;
        liveIndicator.classList.toggle("is-error", isError);
    };

    const refreshDashboard = async () => {
        try {
            const response = await fetch(dashboardConfig.endpoint, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                cache: "no-store",
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const payload = await response.json();
            updateMetrics(payload.metrics);
            renderRecentOrders(payload.recent_orders);
            setIndicatorState("Live");
        } catch (error) {
            setIndicatorState("Retrying", true);
        }
    };

    renderRecentOrders(dashboardConfig.recentOrders || []);
    setIndicatorState("Live");
    window.setInterval(refreshDashboard, dashboardConfig.refreshMs || 15000);
});
