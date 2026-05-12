document.addEventListener('DOMContentLoaded', () => {
    const globalStatus = document.getElementById('global-status');
    const statusText = document.getElementById('status-text');
    const currentVendor = document.getElementById('current-vendor');
    const startTime = document.getElementById('start-time');
    const currentStep = document.getElementById('current-step');
    
    const statProcessed = document.getElementById('stat-processed');
    const statAmount = document.getElementById('stat-amount');
    const statSuccess = document.getElementById('stat-success');
    
    const invoiceTableBody = document.getElementById('invoice-table-body');
    const emptyState = document.getElementById('empty-state');

    // Keep track of rendered IDs so we only add new ones. 
    // Key is inv.id + inv.run_time to handle historical duplicates.
    let renderedInvoices = new Set();

    async function fetchStatus() {
        try {
            // Append timestamp to prevent caching
            const response = await fetch('status.json?t=' + new Date().getTime());
            if (!response.ok) return;
            
            const data = await response.json();
            updateDashboard(data);
        } catch (error) {
            console.log("Waiting for status.json...");
        }
    }

    function updateDashboard(data) {
        // Update Run Details
        const run = data.current_run;
        if (run) {
            currentVendor.innerText = run.vendor !== "None" ? run.vendor.replace('_', ' ') : "None";
            currentStep.innerText = run.step || "Idle";
            
            if (run.start_time) {
                const start = new Date(run.start_time);
                startTime.innerText = start.toLocaleTimeString();
            }

            // Update Status Badge
            if (run.status === "Running") {
                globalStatus.className = "status-badge running";
                statusText.innerText = "Running - Live";
            } else if (run.status === "Completed") {
                globalStatus.className = "status-badge success";
                statusText.innerText = "Completed";
            } else if (run.status === "Failed") {
                globalStatus.className = "status-badge failed";
                statusText.innerText = "Failed";
            } else {
                globalStatus.className = "status-badge";
                statusText.innerText = "Idle";
            }
        }

        // Update Stats (Aggregate All-Time)
        const stats = data.stats;
        if (stats) {
            statProcessed.innerText = stats.total_processed;
            // For aggregate total amount, we default to USD for display but individual rows show correct currency
            statAmount.innerText = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(stats.total_amount);
            statSuccess.innerText = `${stats.success_rate}%`;
        }

        // Update Table
        const invoices = data.invoices || [];
        if (invoices.length > 0) {
            emptyState.style.display = 'none';
            
            // Process in reverse order (oldest to newest in the JSON array)
            // so that prepending results in newest at the top.
            for (let i = invoices.length - 1; i >= 0; i--) {
                const inv = invoices[i];
                const uniqueKey = `${inv.id}_${inv.run_time}`;
                
                if (!renderedInvoices.has(uniqueKey)) {
                    renderedInvoices.add(uniqueKey);
                    
                    const tr = document.createElement('tr');
                    tr.className = 'fade-in';
                    
                    // Dynamic currency formatting based on extracted data
                    const currencyCode = inv.currency || 'USD';
                    const amountFormatted = new Intl.NumberFormat('en-US', { 
                        style: 'currency', 
                        currency: currencyCode 
                    }).format(inv.amount || 0);
                    
                    const runTimeFormatted = new Date(inv.run_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
                    
                    const downloadLink = inv.download_url 
                        ? `<a href="${inv.download_url}" download class="action-btn">Download</a>`
                        : `<span class="action-btn disabled">N/A</span>`;

                    const statusLabel = inv.status === 'success' ? 'SUCCESS' : 'FAILED';
                    const statusClass = inv.status === 'success' ? 'success' : 'failed';

                    tr.innerHTML = `
                        <td class="invoice-id">${inv.id}</td>
                        <td style="font-family: monospace; font-size: 0.85rem; color: var(--text-muted);">${inv.run_id || 'N/A'}</td>
                        <td>${inv.date}</td>
                        <td>${inv.vendor}</td>
                        <td style="text-align: right;" class="amount">${amountFormatted}</td>
                        <td style="font-size: 0.8rem; color: var(--text-muted);">${runTimeFormatted}</td>
                        <td><span class="badge ${statusClass}">${statusLabel}</span></td>
                        <td>${downloadLink}</td>
                    `;
                    
                    // Add to top of table
                    if (invoiceTableBody.firstChild) {
                        invoiceTableBody.insertBefore(tr, invoiceTableBody.firstChild);
                    } else {
                        invoiceTableBody.appendChild(tr);
                    }
                }
            }
        }
    }

    // Poll every 1 second
    setInterval(fetchStatus, 1000);
    // Initial fetch
    fetchStatus();
});
