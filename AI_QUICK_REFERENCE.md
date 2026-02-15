# AI System Quick Reference Card

## 🎯 5 MAIN AI PAGES

### 1️⃣ AI MODEL MANAGEMENT
**URL**: `/inventory/ai-model-management/`  
**Purpose**: Train AI models  
**Action**: Click "Train All Models" button  
**When**: First time, then monthly  
**Shows**: Which items have AI, accuracy %

---

### 2️⃣ AI REORDER (Full AI Analysis)
**URL**: `/inventory/reorder-suggestions/`  
**Purpose**: See what to order  
**Action**: Review alerts, place orders  
**When**: Daily check  
**Shows**: Items needing reorder, predicted demand, urgency

---

### 3️⃣ AI DEMAND FORECAST
**URL**: `/inventory/ai-demand-forecast/[item-id]/`  
**Purpose**: Detailed forecast for 1 item  
**Action**: Review day-by-day predictions  
**When**: Deep dive on specific items  
**Shows**: 14-day forecast, accuracy, model info

---

### 4️⃣ ANALYTICS DASHBOARD
**URL**: `/inventory/analytics-dashboard/`  
**Purpose**: Visual charts and graphs  
**Action**: Review trends  
**When**: Weekly/monthly  
**Shows**: Sales trends, AI accuracy charts, inventory performance

---

### 5️⃣ ITEM ANALYTICS
**URL**: `/inventory/item-analytics/[item-id]/`  
**Purpose**: Charts for 1 specific item  
**Action**: Analyze individual item  
**When**: Item-specific review  
**Shows**: Item's actual vs predicted, transaction history

---

## 🔄 3-STEP WORKFLOW

```
STEP 1: TRAIN
Go to: AI Model Management
Click: "Train All Models"
Wait: 30 seconds
Result: AI models ready

↓

STEP 2: CHECK
Go to: AI Reorder
Look at: Critical/High alerts
Note: Suggested quantities
Result: Know what to order

↓

STEP 3: ORDER
Place orders based on AI suggestions
Record transactions
Result: Prevent stockouts
```

---

## 🚨 URGENCY LEVELS

| Level | Color | Meaning | Action |
|-------|-------|---------|--------|
| **CRITICAL** | 🔴 Red | Out of stock NOW | Order immediately |
| **HIGH** | 🟡 Yellow | Will run out soon | Order today |
| **MEDIUM** | 🔵 Blue | Low stock | Order this week |
| **LOW** | 🟢 Green | Stock is fine | No action needed |

---

## 📊 UNDERSTANDING AI ACCURACY

```
90-100% = Excellent ✅ Trust completely
80-89%  = Good ✅ Reliable predictions  
70-79%  = Fair ⚠️ Use with caution
<70%    = Poor ❌ Need more data
```

---

## 🎓 WHAT EACH PAGE TELLS YOU

### Dashboard (Home)
- AI Intelligence widget
- Critical/High alert counts
- AI coverage percentage
- Quick action buttons

### Inventory List
- AI notification banner
- "🤖 AI Critical" filter
- Stock status for all items
- Reorder suggestions count

### AI Reorder Page
- All items needing reorder
- AI predictions for each
- Urgency classification
- Suggested order quantities
- Model accuracy

### AI Model Management
- Training status per item
- Recent sales count
- Can train? (Yes/No)
- Train buttons
- System summary

### Analytics Dashboard
- Sales trend graph (30 days)
- Actual vs predicted chart
- Inventory performance bars
- AI model accuracy chart

---

## 💡 QUICK TIPS

**For Daily Use:**
1. Check dashboard for AI alerts
2. Visit AI Reorder page
3. Order critical/high items

**For Weekly Review:**
1. Check Analytics Dashboard
2. Review sales trends
3. Verify AI accuracy

**For Monthly Maintenance:**
1. Retrain all AI models
2. Review accuracy percentages
3. Adjust reorder levels if needed

**For Supervisor Demo:**
1. Show AI Model Management (training)
2. Show AI Reorder (predictions)
3. Show Analytics (visual charts)
4. Explain accuracy percentages

---

## 🔢 KEY NUMBERS TO KNOW

- **7 sales** = Minimum to train AI
- **90 days** = Historical data window
- **7 days** = Default forecast period
- **14 days** = Extended forecast period
- **80%+** = Good accuracy threshold

---

## 🎯 ONE-SENTENCE SUMMARIES

**AI Model Management**: "Where you train the AI"

**AI Reorder**: "What to order and when"

**AI Demand Forecast**: "Detailed predictions for one item"

**Analytics Dashboard**: "Visual charts and graphs"

**Item Analytics**: "Charts for specific item"

---

## 📱 NAVIGATION SHORTCUTS

From any page, click:
- **AI Reorder** (nav menu) → Reorder suggestions
- **Analytics** (nav menu) → Analytics dashboard
- **Inventory** → Item list → AI Critical filter
- **Dashboard** → AI Intelligence widget → Quick links

---

## ✅ CHECKLIST: IS AI WORKING?

- [ ] Trained at least one model
- [ ] See accuracy percentage (80%+)
- [ ] AI Reorder page shows predictions
- [ ] Dashboard shows AI widget
- [ ] Alerts appear on pages
- [ ] Analytics charts display

If all checked ✅ = AI is working perfectly!

---

## 🆘 TROUBLESHOOTING

**Problem**: No AI models trained  
**Solution**: Go to AI Model Management, click "Train All Models"

**Problem**: Item shows "Cannot train"  
**Solution**: Item needs 7+ sales in last 90 days

**Problem**: Low accuracy (<70%)  
**Solution**: Record more transactions, retrain monthly

**Problem**: No predictions showing  
**Solution**: Train models first, then check AI Reorder page

**Problem**: Predictions seem wrong  
**Solution**: Check accuracy %, retrain models, verify transaction data

---

## 🎓 ACADEMIC EXPLANATION (For Supervisor)

**Technology**: scikit-learn Linear Regression  
**Algorithm**: Machine Learning (supervised learning)  
**Features**: Day of week, seasonality, time trends  
**Training Data**: Historical sales transactions  
**Output**: Demand predictions with confidence intervals  
**Validation**: Mean Absolute Error (MAE), accuracy percentage  
**Update Frequency**: Monthly retraining recommended  

**Business Value**:
- Proactive inventory management
- Reduced stockouts
- Optimized ordering
- Data-driven decisions
- Cost savings

---

**Print this page for quick reference!** 📄