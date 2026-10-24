import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import { api } from '../services/api'

export const fetchInvestigations = createAsyncThunk('inv/list', async ({ q, status }: any) => api.list(q, status))
export const fetchInvestigation = createAsyncThunk('inv/get', async (id: string) => api.get(id))
export const fetchCapa = createAsyncThunk('capa/list', async (params: string) => api.listCapa(params))
export const runExtract = createAsyncThunk('ai/extract', async ({ text, type }: any) => api.extract(text, type))
export const runAnalyze = createAsyncThunk('ai/analyze', async ({ text, type, id }: any) => api.analyze(text, type, id))

const invSlice = createSlice({
  name: 'investigations', initialState: { items: [] as any[], current: null as any, loading: false, error: '' as string },
  reducers: { setCurrent: (s, a) => { s.current = a.payload } },
  extraReducers: (b) => {
    b.addCase(fetchInvestigations.pending, (s) => { s.loading = true; s.error = '' })
    b.addCase(fetchInvestigations.fulfilled, (s, a) => { s.loading = false; s.items = a.payload.items || [] })
    b.addCase(fetchInvestigations.rejected, (s, a) => { s.loading = false; s.error = String(a.error.message) })
    b.addCase(fetchInvestigation.pending, (s) => { s.loading = true; s.error = '' })
    b.addCase(fetchInvestigation.fulfilled, (s, a) => { s.loading = false; s.current = a.payload })
    b.addCase(fetchInvestigation.rejected, (s, a) => { s.loading = false; s.error = String(a.error.message) })
  },
})
const aiSlice = createSlice({
  name: 'ai', initialState: { extraction: null as any, analysis: null as any, loading: false, error: '' as string },
  reducers: { setAnalysis: (s, a) => { s.analysis = a.payload }, clearAi: (s) => { s.extraction = null; s.analysis = null; s.error = '' } },
  extraReducers: (b) => {
    b.addCase(runExtract.pending, (s) => { s.loading = true; s.error = '' })
    b.addCase(runExtract.fulfilled, (s, a) => { s.loading = false; s.extraction = a.payload.extraction })
    b.addCase(runExtract.rejected, (s, a) => { s.loading = false; s.error = String(a.error.message) })
    b.addCase(runAnalyze.pending, (s) => { s.loading = true; s.error = '' })
    b.addCase(runAnalyze.fulfilled, (s, a) => { s.loading = false; s.analysis = a.payload; s.extraction = a.payload.extraction })
    b.addCase(runAnalyze.rejected, (s, a) => { s.loading = false; s.error = String(a.error.message) })
  },
})
const capaSlice = createSlice({
  name: 'capa', initialState: { items: [] as any[], loading: false, error: '' as string },
  reducers: {},
  extraReducers: (b) => {
    b.addCase(fetchCapa.pending, (s) => { s.loading = true })
    b.addCase(fetchCapa.fulfilled, (s, a) => { s.loading = false; s.items = a.payload.items || [] })
    b.addCase(fetchCapa.rejected, (s, a) => { s.loading = false; s.error = String(a.error.message) })
  },
})
export const { setCurrent } = invSlice.actions
export const { setAnalysis, clearAi } = aiSlice.actions
export const reducers = { investigations: invSlice.reducer, ai: aiSlice.reducer, capa: capaSlice.reducer }
