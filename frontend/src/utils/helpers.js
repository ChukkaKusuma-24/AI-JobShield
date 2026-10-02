export const DISCLAIMER =
  'AI JobShield gives guidance, not a verdict. Always verify through official channels.';

export function riskBadgeClass(level) {
  const l = (level || '').toUpperCase();
  if (l === 'HIGH') return 'badge bg-danger/15 text-danger';
  if (l === 'MEDIUM') return 'badge bg-warn/15 text-warn';
  if (l === 'LOW') return 'badge bg-safe/15 text-safe';
  return 'badge bg-ink/10 text-ink/70';
}

export function severityClass(sev) {
  const s = (sev || '').toLowerCase();
  if (s === 'critical') return 'border-danger/40 bg-danger/5';
  if (s === 'high') return 'border-warn/40 bg-warn/5';
  if (s === 'medium') return 'border-accent/30 bg-accent/5';
  return 'border-ink/10 bg-mist/60';
}

export function companyStatusClass(status) {
  const s = (status || '').toUpperCase();
  if (s === 'VERIFIED') return 'badge bg-safe/15 text-safe';
  if (s === 'PARTIALLY VERIFIED') return 'badge bg-accent/15 text-accent';
  if (s === 'NOT VERIFIED') return 'badge bg-danger/15 text-danger';
  return 'badge bg-ink/10 text-ink/70';
}

export const SAMPLE_SCAM = {
  title: 'Work From Home Data Entry – Instant Selection',
  company_name: 'Quick Cash Careers',
  description:
    'URGENT hiring! Work from home and earn 5000/day. No interview needed. Pay registration fee of 1499 via UPI to join. Contact on WhatsApp only. Guaranteed job for freshers. Limited seats apply within 24 hours. Send Aadhaar and bank details to hr1@gmail.com.',
  salary: '₹5000/day',
  email: 'hr1@gmail.com',
  url: 'http://quick-cash-jobs.xyz/apply',
  location: 'Remote',
  job_type: 'Part-time',
};

export const SAMPLE_LEGIT = {
  title: 'Software Engineer Intern',
  company_name: 'Infosys',
  description:
    'We are hiring a Software Engineer Intern at Infosys. Responsibilities include collaborating with the product team, writing clean code, and participating in code reviews. Qualifications: currently enrolled CS student, knowledge of Python or JavaScript. Stipend 25000/month based on location. Interview process: online assessment, technical round, HR round. Apply via careers@infosys.com or visit https://www.infosys.com/careers. No fees at any stage.',
  salary: '₹25,000/month',
  email: 'careers@infosys.com',
  url: 'https://www.infosys.com/careers',
  location: 'Bengaluru',
  job_type: 'Internship',
};
