module.exports = async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { email, listType } = req.body;

    if (!email || !listType) {
      return res.status(400).json({ error: 'Email and listType are required' });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ error: 'Invalid email format' });
    }

    // Get the appropriate list ID
    let listId;
    if (listType === 'waitlist') {
      listId = 'd17c356e-9d3d-11f0-8a1d-dbd83c3e763c'; // InceptAI Waitlist
    } else if (listType === 'newsletter') {
      listId = 'd80dd6a8-9d3d-11f0-b318-a11313900aca'; // InceptAI Newsletter
    } else {
      return res.status(400).json({ error: 'Invalid listType. Must be "waitlist" or "newsletter"' });
    }

    // Get API key from environment variables
    const apiKey = process.env.EMAILOCTOPUS_API_KEY;
    if (!apiKey) {
      console.error('EMAILOCTOPUS_API_KEY environment variable not set');
      return res.status(500).json({ error: 'Server configuration error' });
    }

    // Subscribe to EmailOctopus
    const response = await fetch(`https://emailoctopus.com/api/1.6/lists/${listId}/contacts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        api_key: apiKey,
        email_address: email,
        status: 'SUBSCRIBED'
      }),
    });

    if (response.ok) {
      const data = await response.json();
      res.status(200).json({
        success: true,
        message: listType === 'waitlist'
          ? 'Thanks! You\'ve been added to the waitlist.'
          : 'Thanks! You\'ve been subscribed to our newsletter.',
        contactId: data.id
      });
    } else {
      const errorData = await response.json();

      // Handle common EmailOctopus errors
      if (errorData.error && errorData.error.code === 'MEMBER_EXISTS_WITH_EMAIL_ADDRESS') {
        res.status(409).json({
          error: 'This email is already subscribed.',
          code: 'ALREADY_SUBSCRIBED'
        });
      } else {
        console.error('EmailOctopus API error:', errorData);
        res.status(400).json({
          error: errorData.error?.message || 'Failed to subscribe. Please try again.',
          code: 'SUBSCRIPTION_FAILED'
        });
      }
    }
  } catch (error) {
    console.error('Subscription error:', error);
    res.status(500).json({
      error: 'Internal server error. Please try again later.',
      code: 'SERVER_ERROR'
    });
  }
};