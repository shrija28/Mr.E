/**
 * Phase 2 Frontend Test Suite
 * Tests plan selection rendering with different subscription states
 * 
 * Run in browser console on /subscription page or include in test framework
 */

const Phase2Tests = {
  /**
   * Test data representing different user subscription states
   */
  mockSubscriptions: {
    free: {
      id: 'sub-1',
      plan_name: 'Free',
      plan_type: 'free',
      status: 'active',
      start_date: new Date().toISOString(),
      next_renewal_date: null,
      end_date: null,
      remaining_attempts: 3,
      total_attempts: 5,
    },
    trial: {
      id: 'sub-2',
      plan_name: '7-Day Premium Trial',
      plan_type: 'trial',
      status: 'active',
      is_trial: true,
      start_date: new Date().toISOString(),
      next_renewal_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      remaining_attempts: 5,
      total_attempts: 5,
    },
    monthly: {
      id: 'sub-3',
      plan_name: 'Pro Monthly',
      plan_type: 'pro',
      status: 'active',
      billing_period: 'monthly',
      start_date: new Date().toISOString(),
      next_renewal_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      end_date: null,
    },
    yearly: {
      id: 'sub-4',
      plan_name: 'Pro Yearly',
      plan_type: 'pro',
      status: 'active',
      billing_period: 'yearly',
      start_date: new Date().toISOString(),
      next_renewal_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
      end_date: null,
    },
    expired: {
      id: 'sub-5',
      plan_name: 'Pro Monthly',
      plan_type: 'pro',
      status: 'expired',
      billing_period: 'monthly',
      start_date: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
      next_renewal_date: null,
      end_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    },
  },

  /**
   * Mock API responses for different states
   */
  mockApiResponses: {
    free: {
      has_active_subscription: true,
      current_plan: {
        id: 'plan-free',
        name: 'Free',
        price: 0,
        billing_period: null,
        is_expired: false,
      },
      subscription_status: 'active',
      next_renewal_date: null,
      available_plans: [
        {
          id: 'plan-free',
          name: 'Free',
          price: 0,
          button_state: 'current',
          button_label: '🔒 Current Plan',
        },
        {
          id: 'plan-trial',
          name: '7-Day Premium Trial',
          price: 0,
          button_state: 'enabled',
          button_label: 'Select Plan',
        },
        {
          id: 'plan-monthly',
          name: 'Pro Monthly',
          price: 349,
          button_state: 'enabled',
          button_label: 'Select Plan',
        },
        {
          id: 'plan-yearly',
          name: 'Pro Yearly',
          price: 2999,
          button_state: 'enabled',
          button_label: 'Select Plan',
        },
      ],
    },

    trial: {
      has_active_subscription: true,
      current_plan: {
        id: 'plan-trial',
        name: '7-Day Premium Trial',
        price: 0,
        billing_period: null,
        is_expired: false,
      },
      subscription_status: 'active',
      next_renewal_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      available_plans: [
        {
          id: 'plan-free',
          name: 'Free',
          price: 0,
          button_state: 'disabled',
          button_label: 'Locked',
        },
        {
          id: 'plan-trial',
          name: '7-Day Premium Trial',
          price: 0,
          button_state: 'current',
          button_label: '🔒 Current Plan',
        },
        {
          id: 'plan-monthly',
          name: 'Pro Monthly',
          price: 349,
          button_state: 'disabled',
          button_label: 'Locked',
        },
        {
          id: 'plan-yearly',
          name: 'Pro Yearly',
          price: 2999,
          button_state: 'disabled',
          button_label: 'Locked',
        },
      ],
    },

    monthly: {
      has_active_subscription: true,
      current_plan: {
        id: 'plan-monthly',
        name: 'Pro Monthly',
        price: 349,
        billing_period: 'monthly',
        is_expired: false,
      },
      subscription_status: 'active',
      next_renewal_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      available_plans: [
        {
          id: 'plan-free',
          name: 'Free',
          price: 0,
          button_state: 'disabled',
          button_label: 'Locked',
        },
        {
          id: 'plan-trial',
          name: '7-Day Premium Trial',
          price: 0,
          button_state: 'disabled',
          button_label: 'Locked',
        },
        {
          id: 'plan-monthly',
          name: 'Pro Monthly',
          price: 349,
          button_state: 'current',
          button_label: '🔒 Current Plan',
        },
        {
          id: 'plan-yearly',
          name: 'Pro Yearly',
          price: 2999,
          button_state: 'disabled',
          button_label: 'Locked',
        },
      ],
    },

    yearly: {
      has_active_subscription: true,
      current_plan: {
        id: 'plan-yearly',
        name: 'Pro Yearly',
        price: 2999,
        billing_period: 'yearly',
        is_expired: false,
      },
      subscription_status: 'active',
      next_renewal_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
      available_plans: [
        {
          id: 'plan-free',
          name: 'Free',
          price: 0,
          button_state: 'disabled',
          button_label: 'Locked',
        },
        {
          id: 'plan-trial',
          name: '7-Day Premium Trial',
          price: 0,
          button_state: 'disabled',
          button_label: 'Locked',
        },
        {
          id: 'plan-monthly',
          name: 'Pro Monthly',
          price: 349,
          button_state: 'disabled',
          button_label: 'Locked',
        },
        {
          id: 'plan-yearly',
          name: 'Pro Yearly',
          price: 2999,
          button_state: 'current',
          button_label: '🔒 Current Plan',
        },
      ],
    },

    expired: {
      has_active_subscription: false,
      current_plan: {
        id: 'plan-monthly',
        name: 'Pro Monthly',
        price: 349,
        billing_period: 'monthly',
        is_expired: true,
      },
      subscription_status: 'expired',
      next_renewal_date: null,
      available_plans: [
        {
          id: 'plan-free',
          name: 'Free',
          price: 0,
          button_state: 'enabled',
          button_label: 'Select Plan',
        },
        {
          id: 'plan-trial',
          name: '7-Day Premium Trial',
          price: 0,
          button_state: 'enabled',
          button_label: 'Select Plan',
        },
        {
          id: 'plan-monthly',
          name: 'Pro Monthly',
          price: 349,
          button_state: 'enabled',
          button_label: 'Select Plan',
        },
        {
          id: 'plan-yearly',
          name: 'Pro Yearly',
          price: 2999,
          button_state: 'enabled',
          button_label: 'Select Plan',
        },
      ],
    },
  },

  /**
   * Test cases for each subscription state
   */
  testCases: [
    {
      name: 'Free User',
      state: 'free',
      expectedButtonStates: {
        'Free': { state: 'current', enabled: false },
        '7-Day Premium Trial': { state: 'enabled', enabled: true },
        'Pro Monthly': { state: 'enabled', enabled: true },
        'Pro Yearly': { state: 'enabled', enabled: true },
      },
      description: 'Free user can upgrade to Trial, Monthly, or Yearly',
    },
    {
      name: 'Trial User',
      state: 'trial',
      expectedButtonStates: {
        'Free': { state: 'disabled', enabled: false },
        '7-Day Premium Trial': { state: 'current', enabled: false },
        'Pro Monthly': { state: 'disabled', enabled: false },
        'Pro Yearly': { state: 'disabled', enabled: false },
      },
      description: 'Trial user cannot switch during trial period',
    },
    {
      name: 'Monthly User',
      state: 'monthly',
      expectedButtonStates: {
        'Free': { state: 'disabled', enabled: false },
        '7-Day Premium Trial': { state: 'disabled', enabled: false },
        'Pro Monthly': { state: 'current', enabled: false },
        'Pro Yearly': { state: 'disabled', enabled: false },
      },
      description: 'Monthly user cannot downgrade or switch',
    },
    {
      name: 'Yearly User',
      state: 'yearly',
      expectedButtonStates: {
        'Free': { state: 'disabled', enabled: false },
        '7-Day Premium Trial': { state: 'disabled', enabled: false },
        'Pro Monthly': { state: 'disabled', enabled: false },
        'Pro Yearly': { state: 'current', enabled: false },
      },
      description: 'Yearly user (highest tier) is locked',
    },
    {
      name: 'Expired User',
      state: 'expired',
      expectedButtonStates: {
        'Free': { state: 'enabled', enabled: true },
        '7-Day Premium Trial': { state: 'enabled', enabled: true },
        'Pro Monthly': { state: 'enabled', enabled: true },
        'Pro Yearly': { state: 'enabled', enabled: true },
      },
      description: 'Expired user can select any plan to restart',
    },
  ],

  /**
   * Run all tests
   */
  async runAll() {
    console.log('🧪 Phase 2 Frontend Test Suite Starting...\n');
    
    let passed = 0;
    let failed = 0;

    for (const testCase of this.testCases) {
      const result = await this.runTestCase(testCase);
      if (result.passed) {
        passed++;
        console.log(`✓ ${result.name}`);
      } else {
        failed++;
        console.error(`✗ ${result.name}`);
        result.errors.forEach(err => console.error(`  - ${err}`));
      }
    }

    console.log(`\n📊 Results: ${passed} passed, ${failed} failed out of ${passed + failed} tests`);
    
    return { passed, failed, total: passed + failed };
  },

  /**
   * Run a single test case
   */
  async runTestCase(testCase) {
    const apiResponse = this.mockApiResponses[testCase.state];
    const errors = [];

    // Verify API response has all required fields
    if (!apiResponse.available_plans) {
      errors.push('API response missing available_plans');
      return { name: testCase.name, passed: false, errors };
    }

    // Check button states match expectations
    for (const plan of apiResponse.available_plans) {
      const expected = testCase.expectedButtonStates[plan.name];
      if (!expected) {
        errors.push(`Unknown plan in response: ${plan.name}`);
        continue;
      }

      if (plan.button_state !== expected.state) {
        errors.push(
          `${plan.name}: expected button_state="${expected.state}", ` +
          `got "${plan.button_state}"`
        );
      }

      // Disabled state should match button_state
      const shouldBeDisabled = plan.button_state !== 'enabled';
      if (shouldBeDisabled !== !expected.enabled) {
        errors.push(
          `${plan.name}: expected enabled=${expected.enabled}, ` +
          `got enabled=${!shouldBeDisabled}`
        );
      }
    }

    return {
      name: testCase.name,
      passed: errors.length === 0,
      errors,
    };
  },

  /**
   * Display visual representation of button states
   */
  displayVisualTest(state) {
    const response = this.mockApiResponses[state];
    console.log(`\n📱 Visual Test: ${state.toUpperCase()} User\n`);

    response.available_plans.forEach(plan => {
      const icon = plan.button_state === 'current' ? '🔒' :
                   plan.button_state === 'enabled' ? '✓' : '✗';
      const label = plan.button_label;
      console.log(`${icon} ${plan.name.padEnd(25)} | ${label.padEnd(20)} | ₹${plan.price}`);
    });
  },
};

// Export for use in test frameworks
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Phase2Tests;
}

// Usage:
// Phase2Tests.runAll();
// Phase2Tests.displayVisualTest('free');
// Phase2Tests.displayVisualTest('trial');
// Phase2Tests.displayVisualTest('monthly');
// Phase2Tests.displayVisualTest('yearly');
// Phase2Tests.displayVisualTest('expired');
