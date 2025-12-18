# UI Component Architecture - Core Systems Needed

## Problem
Currently there's code duplication across components (App.tsx, DashboardPage.tsx) and no consistent design system.

## Solution: Create Reusable Core Components

### ✅ COMPLETED

#### 1. WorkflowCard Component
**File:** `ui/src/ui/components/WorkflowCard.tsx`

**Features:**
- Reusable workflow card with gradient backgrounds
- Icon-based (BookOpen from lucide-react, not emoji)
- Spinner badge for in-progress workflows
- Dashed border around title when generating
- Consistent sizing (aspect-[2/3])

**Usage:**
```tsx
<WorkflowCard workflow={workflow} index={idx} />
```

---

## 🔧 NEEDED: Core Component Library

### 2. Badge Component
**Purpose:** Consistent badges for status, stages, counts

**File:** `ui/src/ui/components/Badge.tsx`

```tsx
interface BadgeProps {
  variant: 'default' | 'orange' | 'success' | 'warning' | 'error';
  children: React.ReactNode;
  icon?: React.ReactNode;
}

// Usage:
<Badge variant="orange">GENERATING</Badge>
<Badge variant="success" icon={<Check />}>COMPLETE</Badge>
```

**Used in:**
- Workflow cards (stage badges)
- Chapter cards (status)
- Page cards (status)

---

### 3. Card Component
**Purpose:** Consistent card styling across the app

**File:** `ui/src/ui/components/Card.tsx`

```tsx
interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

// Usage:
<Card padding="lg">
  <h2>Content</h2>
</Card>
```

**Used in:**
- Dashboard sections
- Workflow details
- Chapter/page lists

---

### 4. Button Component
**Purpose:** Consistent button styles

**File:** `ui/src/ui/components/Button.tsx`

```tsx
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  loading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

// Usage:
<Button variant="primary" icon={<Plus />} loading={isLoading}>
  CREATE WORKFLOW
</Button>
```

**Used in:**
- Create workflow form
- Generation controls
- Navigation

---

### 5. Spinner/Loader Component
**Purpose:** Consistent loading states

**File:** `ui/src/ui/components/Spinner.tsx`

```tsx
interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'orange' | 'white';
}

// Usage:
<Spinner size="lg" variant="orange" />
```

**Used in:**
- Workflow cards (generating badge)
- Loading states
- Button loading states

---

### 6. ChapterCard Component
**Purpose:** Reusable chapter display

**File:** `ui/src/ui/components/ChapterCard.tsx`

```tsx
interface ChapterCardProps {
  chapter: ChapterSummary;
  selected?: boolean;
  onClick?: () => void;
}

// Usage:
<ChapterCard 
  chapter={chapter} 
  selected={selectedChapter === chapter.chapterNumber}
  onClick={() => setSelectedChapter(chapter.chapterNumber)}
/>
```

**Used in:**
- Workflow page (chapter list)
- Dashboard (chapter previews)

---

### 7. PageCard Component
**Purpose:** Reusable page display

**File:** `ui/src/ui/components/PageCard.tsx`

```tsx
interface PageCardProps {
  page: PageSummary;
  showImage?: boolean;
  onClick?: () => void;
}

// Usage:
<PageCard page={page} showImage={true} />
```

**Used in:**
- Workflow page (page list)
- Chapter detail view

---

### 8. StatusIndicator Component
**Purpose:** Visual status indicators

**File:** `ui/src/ui/components/StatusIndicator.tsx`

```tsx
interface StatusIndicatorProps {
  status: 'pending' | 'running' | 'completed' | 'failed';
  label?: string;
}

// Usage:
<StatusIndicator status="running" label="Generating..." />
```

**Used in:**
- Job status displays
- Workflow progress
- Generation controls

---

### 9. EmptyState Component
**Purpose:** Consistent empty states

**File:** `ui/src/ui/components/EmptyState.tsx`

```tsx
interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Usage:
<EmptyState
  icon={<BookOpen />}
  title="No workflows yet"
  description="Create your first comic"
  action={{ label: "Create Workflow", onClick: handleCreate }}
/>
```

**Used in:**
- Empty workflow list
- Empty chapter list
- Empty page list

---

### 10. Header Component
**Purpose:** Consistent page headers

**File:** `ui/src/ui/components/Header.tsx`

```tsx
interface HeaderProps {
  title: string;
  badge?: string;
  actions?: React.ReactNode;
}

// Usage:
<Header 
  title="COMICS BOOK" 
  badge={`${workflows.length} PROJECTS`}
  actions={<Button>New</Button>}
/>
```

**Used in:**
- Dashboard header
- Workflow page header

---

## 🎨 Design System Tokens

### File: `ui/src/ui/styles/tokens.ts`

```typescript
export const colors = {
  ink: 'var(--ink)',
  paper: 'var(--paper)',
  cream: 'var(--cream)',
  creamDark: 'var(--cream-dark)',
  orange: 'var(--orange)',
  yellow: 'var(--yellow)',
  red: 'var(--red)',
  muted: 'var(--muted)',
};

export const spacing = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
};

export const borderRadius = {
  sm: '0.25rem',
  md: '0.5rem',
  lg: '0.75rem',
  full: '9999px',
};
```

---

## 📦 Icon System

### File: `ui/src/ui/components/icons/index.ts`

```typescript
// Re-export commonly used icons from lucide-react
export {
  BookOpen,
  FileText,
  Image,
  Loader2,
  Plus,
  Check,
  X,
  ChevronRight,
  ChevronLeft,
  Settings,
  Download,
  Upload,
  Trash2,
  Edit,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
} from 'lucide-react';
```

**Usage:**
```tsx
import { BookOpen, Loader2 } from '@/ui/components/icons';
```

---

## 🔄 State Management

### File: `ui/src/ui/hooks/useWorkflows.ts`

```typescript
export const useWorkflows = () => {
  const api = useApi();
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadWorkflows = async () => {
    // ... implementation
  };

  const createWorkflow = async (data: CreateWorkflowRequest) => {
    // ... implementation
  };

  return { workflows, loading, error, loadWorkflows, createWorkflow };
};
```

---

## 📁 Recommended File Structure

```
ui/src/ui/
├── components/
│   ├── Badge.tsx                 ✅ NEEDED
│   ├── Button.tsx                ✅ NEEDED
│   ├── Card.tsx                  ✅ NEEDED
│   ├── ChapterCard.tsx           ✅ NEEDED
│   ├── CreateWorkflowForm.tsx    ✅ EXISTS
│   ├── EmptyState.tsx            ✅ NEEDED
│   ├── GenerationBar.tsx         ✅ EXISTS
│   ├── Header.tsx                ✅ NEEDED
│   ├── PageCard.tsx              ✅ NEEDED
│   ├── Spinner.tsx               ✅ NEEDED
│   ├── StatusIndicator.tsx       ✅ NEEDED
│   ├── WorkflowCard.tsx          ✅ CREATED
│   └── icons/
│       └── index.ts              ✅ NEEDED
├── hooks/
│   ├── useWorkflows.ts           ✅ NEEDED
│   ├── useChapters.ts            ✅ NEEDED
│   └── usePages.ts               ✅ NEEDED
├── pages/
│   ├── DashboardPage.tsx         ✅ EXISTS
│   ├── WorkflowPage.tsx          ✅ EXISTS
│   └── Landing.tsx               ✅ EXISTS
├── styles/
│   └── tokens.ts                 ✅ NEEDED
└── api/
    ├── ApiClient.ts              ✅ EXISTS
    └── ApiProvider.tsx           ✅ EXISTS
```

---

## 🎯 Priority Order

### Phase 1: Core Components (High Priority)
1. ✅ WorkflowCard - DONE
2. Badge - Status indicators everywhere
3. Button - Consistent actions
4. Spinner - Loading states
5. Card - Layout consistency

### Phase 2: Feature Components (Medium Priority)
6. ChapterCard - Chapter displays
7. PageCard - Page displays
8. EmptyState - Better UX
9. StatusIndicator - Job status
10. Header - Page headers

### Phase 3: System (Low Priority)
11. Design tokens - Centralized styling
12. Icon exports - Easier imports
13. Custom hooks - State management

---

## 🚀 Benefits

### Before (Current State)
- ❌ Code duplication (App.tsx vs DashboardPage.tsx)
- ❌ Emojis instead of proper icons
- ❌ Inconsistent styling
- ❌ Hard to maintain
- ❌ No reusability

### After (With Component System)
- ✅ Single source of truth for each component
- ✅ Proper icon library (lucide-react)
- ✅ Consistent design system
- ✅ Easy to maintain
- ✅ Highly reusable
- ✅ Type-safe props
- ✅ Better developer experience

---

## 📝 Next Steps

1. **Immediate:** Create Badge, Button, Spinner components
2. **Short-term:** Create ChapterCard, PageCard components
3. **Long-term:** Extract design tokens, create custom hooks

---

**Status:** WorkflowCard component created ✅
**Next:** Create Badge, Button, Spinner components
