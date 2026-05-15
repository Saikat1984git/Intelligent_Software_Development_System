/* ============================================================
   mockIncidents.js
   Shape matches the real API exactly.
   knowledge_sources array added — this is what the backend
   returns from the Knowledge Retrieval layer (Layer 3).
   ============================================================ */

export const MOCK_INCIDENTS = [
  {
    id: 'INC0204919',
    affected_user: 'Fayaz Khan',
    config_item: 'Maestro',
    category: 'Application',
    priority: '4-Low',
    state: 'Transferred',
    assignment_group: 'Development – InterraIT',
    escalated_to: '',
    queue: 'Internal IT Support',
    assigned_to: 'Avrajit Sikder',
    created: '08/05/2026 17:41:04',
    sla_due: 'UNKNOWN',
    short_desc: 'FW: Email addresses not recognised',
    ai_analysis: null,
  },
  {
    id: 'INC0204353',
    affected_user: 'Jessica Somers',
    config_item: 'Maestro',
    category: 'Application',
    priority: '4-Low',
    state: 'Transferred',
    assignment_group: 'Development – InterraIT',
    escalated_to: '',
    queue: 'Internal IT Support',
    assigned_to: 'Avrajit Sikder',
    created: '29/04/2026 16:32:45',
    sla_due: 'UNKNOWN',
    short_desc: 'Uploading process documents in Maestro for specific category types',
    ai_analysis: null,
  },
  {
    id: 'INC0205123',
    affected_user: 'Guest',
    config_item: 'Parts',
    category: 'Application',
    priority: '4-Low',
    state: 'Transferred',
    assignment_group: 'Development – InterraIT',
    escalated_to: '',
    queue: 'Internal IT Support',
    assigned_to: 'Avrajit Sikder',
    created: '13/05/2026 16:59:06',
    sla_due: 'UNKNOWN',
    short_desc: 'FW: P51B13290B - NOT LOADING IN VOR PART ORDER ENTRY',
    ai_analysis: null,
  },
  {
    id: 'INC0204457',
    affected_user: 'Rose Boreham',
    config_item: 'Application',
    category: 'Application',
    priority: '4-Low',
    state: 'Transferred',
    assignment_group: 'Development – InterraIT',
    escalated_to: '',
    queue: 'Internal IT Support',
    assigned_to: 'Avrajit Sikder',
    created: '30/04/2026 16:43:52',
    sla_due: 'UNKNOWN',
    short_desc: 'AVIS_FW: [External] Vehicle Tax Invoice WAR1014576',
    ai_analysis: null,
  },
  {
    id: 'INC0203981',
    affected_user: 'Michael Chen',
    config_item: 'VehicleTrack',
    category: 'Data',
    priority: '2-High',
    state: 'Open',
    assignment_group: 'Database Team',
    escalated_to: 'Animesh Prakash',
    queue: 'Internal IT Support',
    assigned_to: 'Saikat Chatterjee',
    created: '25/04/2026 09:14:22',
    sla_due: '26/04/2026 09:14:22',
    short_desc: 'Vehicle stock number 12345 allocated to two users in DEMFO008 table',
    ai_analysis: {
      incident_type: 'Data Inconsistency',
      application: 'Vehicle Allocation System',
      table: 'DEMFO008',
      severity: 'Medium',
      probable_team: 'Application Support / Database Team',

      /* ── Layer 3: Knowledge Retrieval results ── */
      knowledge_sources: [
        {
          type: 'past_ticket',
          title: 'INC0198432 – Duplicate vehicle allocation in TABLE1',
          similarity: 0.94,
          snippet: 'Old user record not removed before new allocation was created. Resolved by running DB cleanup script and adding a pre-insert validation rule.',
          resolved_by: 'Database Team — resolved in 2 days',
        },
        {
          type: 'sop_document',
          title: 'SOP-DB-012: Duplicate record identification and cleanup',
          similarity: 0.81,
          snippet: 'Standard procedure for identifying orphaned allocation records, verifying user status via HR system, and safely deactivating invalid rows.',
          resolved_by: null,
        },
        {
          type: 'known_error',
          title: 'KE-441: Vehicle allocation validation bypass during batch import',
          similarity: 0.76,
          snippet: 'Known issue where the duplicate-allocation check is skipped when records are inserted via the batch import pipeline rather than the UI.',
          resolved_by: null,
        },
        {
          type: 'app_log',
          title: 'Application log pattern: ALLOC_DUPLICATE_WARN',
          similarity: 0.68,
          snippet: 'Log pattern seen in 3 prior incidents. Indicates the validation middleware received the request but returned a soft-warn instead of a hard-block.',
          resolved_by: null,
        },
      ],

      /* ── Layer 4: AI Decision Engine output ── */
      problem_summary: 'Stock number 12345 is allocated to two users in DEMFO008. One user has already left the organisation, but their record was not removed before the new allocation was created.',
      probable_cause: 'The old allocation record was not removed before assigning the vehicle to the new user, or the validation rule did not prevent duplicate allocation — possibly due to the known batch-import bypass (KE-441).',
      confidence: 0.91,
      can_auto_resolve: false,
      needs_approval: true,

      /* ── Layer 6: Guidance output ── */
      recommended_actions: [
        'Validate duplicate records in DEMFO008 using: SELECT * FROM DEMFO008 WHERE stock_number = 12345.',
        'Confirm whether the old user has left the organisation via the HR system.',
        'Check audit history columns: created_by, updated_by, updated_date on both records.',
        'Raise INFRA request to delete or deactivate the invalid old record after business approval.',
        'Ask application team to verify why duplicate allocation validation was bypassed (ref KE-441).',
      ],
      escalation_team: 'Application Support + Database Team',
      resolution_path: 'Estimated 1–2 days. DB cleanup requires business approval. Validation fix requires application team sprint.',
    },
  },
  {
    id: 'INC0204101',
    affected_user: 'Priya Sharma',
    config_item: 'OrderSystem',
    category: 'Performance',
    priority: '3-Moderate',
    state: 'In Progress',
    assignment_group: 'Application Support',
    escalated_to: '',
    queue: 'Internal IT Support',
    assigned_to: 'Ganesh Chandra Kar',
    created: '27/04/2026 11:05:33',
    sla_due: '28/04/2026 11:05:33',
    short_desc: 'Order processing page timing out after 30 seconds for large datasets',
    ai_analysis: null,
  },
];

/* ============================================================
   ai_analysis shape reference (for backend contract):

   {
     incident_type       string
     application         string
     table               string | null
     severity            'Critical' | 'High' | 'Medium' | 'Low'
     probable_team       string
     confidence          number  0.0–1.0   ← decision engine certainty
     can_auto_resolve    bool
     needs_approval      bool
     knowledge_sources: [            ← Layer 3 output
       {
         type        'past_ticket' | 'sop_document' | 'known_error' | 'app_log'
         title       string
         similarity  number 0.0–1.0
         snippet     string
         resolved_by string | null
       }
     ]
     problem_summary     string     ← Layer 4 output
     probable_cause      string
     recommended_actions string[]   ← Layer 6 output
     escalation_team     string
     resolution_path     string | null
   }
   ============================================================ */