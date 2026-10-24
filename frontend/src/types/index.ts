export type FieldVal = { value: string | null; provenance: string; source_excerpt?: string | null }
export type Investigation = {
  id: string; title: string; deviation_reference?: string | null; event_date?: string | null
  manufacturing_stage?: string | null; product_batch?: string | null; site_equipment?: string | null
  description: string; observed_result?: string | null; expected_result?: string | null
  containment_actions?: string | null; impact?: string | null; summary?: string | null
  status: string; source_type?: string | null; source_filename?: string | null; source_text?: string | null
  extracted_json?: any; reviewer_name?: string | null; reviewer_comment?: string | null
  created_at?: string | null; updated_at?: string | null
  evidence: any[]; five_whys: any[]; fishbone: any[]; root_causes: any[]; capas: any[]; reviews: any[]
}
export type Analysis = {
  extraction: Record<string, FieldVal> & { evidence_gaps: string[]; confirmed_observations: string[]; followup_questions: string[] }
  five_whys: any[]; fishbone: any[]; root_causes: any[]; capas: any[]; evidence_checklist: any[]; disclaimer: string
}
export const DISCLAIMER = 'AI-generated findings are investigation suggestions, not verified root causes or approved quality decisions. Review all evidence and conclusions through the applicable quality process.'
export const DEMO_TEXT = `FICTIONAL DEMO DATA — NOT A REAL BATCH OR GMP RECORD

During the final drying stage of a fictional API batch, the recorded moisture result was above the stated internal acceptance criterion. The drying cycle was extended beyond the planned duration in an attempt to bring the result within criterion, but the follow-up result remained above criterion.

The report mentions a potential discrepancy in a temperature sensor record for the dryer during this stage. The actual equipment condition, calibration status of the temperature sensor, material characteristics, and complete batch history have not yet been verified.

Immediate containment noted in the report: the batch was placed on hold pending investigation, and no further processing was performed.

No batch number, date, numerical moisture value, acceptance limit, equipment ID, or personnel name is provided in this fictional report, and none should be assumed.`
export const FISHBONE_CATEGORIES = ['People', 'Equipment', 'Materials', 'Methods', 'Measurement', 'Environment']
export const CHECKLIST = ['Batch manufacturing and processing records', 'Equipment usage, cleaning, and maintenance records', 'Instrument calibration records', 'Raw material and supplier records', 'Environmental monitoring data, where relevant', 'Laboratory analytical results and chromatograms, where relevant', 'Process parameter trends', 'Deviation history and recurrence patterns', 'Personnel training and procedure adherence records', 'Relevant SOPs and approved process instructions']
