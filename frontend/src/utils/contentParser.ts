/**
 * Utility functions to parse and clean AI-generated content
 * for display in the UI.
 */

/**
 * Parses email content and extracts only the relevant parts.
 * Removes metadata, headers, and formatting that shouldn't be displayed.
 */
export function parseEmailContent(email: string): { subject: string | null; body: string } {
  if (!email) {
    return { subject: null, body: '' }
  }

  // Handle case where email is a stringified JSON array (OpenAI response format)
  // Format: "[{'type': 'output_text', 'text': '...'}]" 
  // The API returns this as a JSON string, so we need to parse it twice
  let emailText = email
  
  try {
    // First parse: Remove outer JSON string quotes
    // Input: "[{'type': 'output_text', 'text': '...'}]"
    // Output: "[{'type': 'output_text', 'text': '...'}]" (string without outer quotes)
    let parsed = JSON.parse(email)
    
    // If it's already an array (shouldn't happen but handle it)
    if (Array.isArray(parsed) && parsed.length > 0) {
      const firstItem = parsed[0]
      if (typeof firstItem === 'object' && firstItem !== null) {
        emailText = firstItem.text || firstItem.content || email
      }
    } 
    // If it's a string (the Python-like format), extract the text field
    else if (typeof parsed === 'string') {
      // Find the 'text' field value
      // Pattern: 'text': '...'}] where ... contains escaped characters like \\n
      // Strategy: Find 'text': then find the opening quote, then find the last quote before }]
      
      const textFieldPattern = /'text':\s*'/
      const match = parsed.match(textFieldPattern)
      
      if (match && match.index !== undefined) {
        const quoteStart = match.index + match[0].length - 1 // Position of opening quote
        // Find the last single quote before the closing }]
        const closingBracket = parsed.lastIndexOf("}]")
        if (closingBracket > quoteStart) {
          // Search backwards from the closing bracket to find the last quote
          // This works because the text field is the last field before the closing bracket
          let quoteEnd = closingBracket - 1
          while (quoteEnd > quoteStart && parsed[quoteEnd] !== "'") {
            quoteEnd--
          }
          if (quoteEnd > quoteStart) {
            emailText = parsed.substring(quoteStart + 1, quoteEnd)
          }
        }
      }
      
      // Fallback to regex if the above method didn't work
      if (emailText === email) {
        // Try a more permissive regex that handles the full string
        const textMatch = parsed.match(/'text':\s*'([^']*(?:\\.[^']*)*)'/)
        if (textMatch && textMatch[1]) {
          emailText = textMatch[1]
        } else {
          // Try with double quotes
          const textMatch2 = parsed.match(/"text":\s*"([^"]*(?:\\.[^"]*)*)"/)
          if (textMatch2 && textMatch2[1]) {
            emailText = textMatch2[1]
          }
        }
      }
    }
  } catch {
    // If JSON.parse fails, try direct regex extraction
    // This handles the case where the string isn't properly JSON-encoded
    const textMatch = email.match(/'text':\s*'((?:[^'\\]|\\.)*)'/)
    if (textMatch) {
      emailText = textMatch[1]
    } else {
      const textMatch2 = email.match(/"text":\s*"((?:[^"\\]|\\.)*)"/)
      if (textMatch2) {
        emailText = textMatch2[1]
      }
    }
  }
  
  // Unescape escape sequences
  // Handle \\n (double-escaped) and \n (single-escaped) newlines
  emailText = emailText
    .replace(/\\\\n/g, '\n')  // Double-escaped: \\n -> \n
    .replace(/\\n/g, '\n')    // Single-escaped: \n -> actual newline
    .replace(/\\t/g, '\t')    // Tabs
    .replace(/\\'/g, "'")     // Escaped single quotes
    .replace(/\\"/g, '"')     // Escaped double quotes
    .replace(/\\\\/g, '\\')   // Escaped backslashes (must be last)

  let subject: string | null = null
  let body = emailText

  // Extract subject line if present
  const subjectMatch = emailText.match(/^Subject:\s*(.+)$/mi)
  if (subjectMatch) {
    subject = subjectMatch[1].trim()
    // Remove subject line from body
    body = emailText.replace(/^Subject:\s*.+$/mi, '').trim()
  }

  // Remove common email headers/metadata that might be included
  const headersToRemove = [
    /^From:\s*.+$/mi,
    /^To:\s*.+$/mi,
    /^CC:\s*.+$/mi,
    /^BCC:\s*.+$/mi,
    /^Date:\s*.+$/mi,
    /^Sent:\s*.+$/mi,
    /^Reply-To:\s*.+$/mi,
  ]

  headersToRemove.forEach((pattern) => {
    body = body.replace(pattern, '')
  })

  // Clean up extra whitespace and empty lines
  body = body
    .split('\n')
    .map((line) => line.trim())
    .filter((line, index, array) => {
      // Remove multiple consecutive empty lines
      if (line === '' && array[index + 1] === '') {
        return false
      }
      return true
    })
    .join('\n')
    .trim()

  return { subject, body }
}

/**
 * Cleans social media post content by removing metadata and formatting.
 */
export function cleanPostContent(post: string): string {
  if (!post) {
    return ''
  }

  // Handle case where post is a stringified JSON array (OpenAI response format)
  // Format: "[{'type': 'output_text', 'text': '...'}]" 
  // The API returns this as a JSON string, so we need to parse it twice
  let postText = post
  
  try {
    // First parse: Remove outer JSON string quotes
    // Input: "[{'type': 'output_text', 'text': '...'}]"
    // Output: "[{'type': 'output_text', 'text': '...'}]" (string without outer quotes)
    let parsed = JSON.parse(post)
    
    // If it's already an array (shouldn't happen but handle it)
    if (Array.isArray(parsed) && parsed.length > 0) {
      const firstItem = parsed[0]
      if (typeof firstItem === 'object' && firstItem !== null) {
        postText = firstItem.text || firstItem.content || post
      }
    } 
    // If it's a string (the Python-like format), extract the text field
    else if (typeof parsed === 'string') {
      // Find the 'text' field value
      // Pattern: 'text': '...'}] where ... contains escaped characters like \\n
      // Strategy: Find 'text': then find the opening quote, then find the last quote before }]
      
      const textFieldPattern = /'text':\s*'/
      const match = parsed.match(textFieldPattern)
      
      if (match && match.index !== undefined) {
        const quoteStart = match.index + match[0].length - 1 // Position of opening quote
        // Find the last single quote before the closing }]
        const closingBracket = parsed.lastIndexOf("}]")
        if (closingBracket > quoteStart) {
          // Search backwards from the closing bracket to find the last quote
          // This works because the text field is the last field before the closing bracket
          let quoteEnd = closingBracket - 1
          while (quoteEnd > quoteStart && parsed[quoteEnd] !== "'") {
            quoteEnd--
          }
          if (quoteEnd > quoteStart) {
            postText = parsed.substring(quoteStart + 1, quoteEnd)
          }
        }
      }
      
      // Fallback to regex if the above method didn't work
      if (postText === post) {
        // Try a more permissive regex that handles the full string
        const textMatch = parsed.match(/'text':\s*'([^']*(?:\\.[^']*)*)'/)
        if (textMatch && textMatch[1]) {
          postText = textMatch[1]
        } else {
          // Try with double quotes
          const textMatch2 = parsed.match(/"text":\s*"([^"]*(?:\\.[^"]*)*)"/)
          if (textMatch2 && textMatch2[1]) {
            postText = textMatch2[1]
          }
        }
      }
    }
  } catch {
    // If JSON.parse fails, try direct regex extraction
    // This handles the case where the string isn't properly JSON-encoded
    const textMatch = post.match(/'text':\s*'((?:[^'\\]|\\.)*)'/)
    if (textMatch) {
      postText = textMatch[1]
    } else {
      const textMatch2 = post.match(/"text":\s*"((?:[^"\\]|\\.)*)"/)
      if (textMatch2) {
        postText = textMatch2[1]
      }
    }
  }
  
  // Unescape escape sequences
  // Handle \\n (double-escaped) and \n (single-escaped) newlines
  postText = postText
    .replace(/\\\\n/g, '\n')  // Double-escaped: \\n -> \n
    .replace(/\\n/g, '\n')    // Single-escaped: \n -> actual newline
    .replace(/\\t/g, '\t')    // Tabs
    .replace(/\\'/g, "'")     // Escaped single quotes
    .replace(/\\"/g, '"')     // Escaped double quotes
    .replace(/\\\\/g, '\\')   // Escaped backslashes (must be last)

  let cleaned = postText

  // Remove common prefixes/metadata that AI might add
  const prefixesToRemove = [
    /^\[LinkedIn\]\s*/i,
    /^\[Facebook\]\s*/i,
    /^\[Post\]\s*/i,
    /^Post:\s*/i,
    /^Content:\s*/i,
    /^Social Media Post:\s*/i,
  ]

  prefixesToRemove.forEach((pattern) => {
    cleaned = cleaned.replace(pattern, '')
  })

  // Remove markdown formatting if present (but keep the text)
  cleaned = cleaned
    .replace(/\*\*(.+?)\*\*/g, '$1') // Bold
    .replace(/\*(.+?)\*/g, '$1') // Italic
    .replace(/\[(.+?)\]\(.+?\)/g, '$1') // Links
    .replace(/^#+\s*/gm, '') // Headers
    .replace(/^-\s*/gm, '') // List items (but keep content)
    .replace(/^\d+\.\s*/gm, '') // Numbered lists

  // Clean up extra whitespace
  cleaned = cleaned
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0) // Remove empty lines
    .join(' ')
    .trim()

  // Remove quotes if the entire content is wrapped in quotes
  if ((cleaned.startsWith('"') && cleaned.endsWith('"')) || 
      (cleaned.startsWith("'") && cleaned.endsWith("'"))) {
    cleaned = cleaned.slice(1, -1).trim()
  }

  return cleaned
}

