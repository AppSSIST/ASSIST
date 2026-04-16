# Mobile App API Integration Guide

## Overview
The Django backend now provides API endpoints for your Android (Kotlin/Java) app to access schedule printing and PDF generation.

---

## API Endpoints

### 1. **Get Staff Schedule as HTML** (For WebView Display)
```
GET /api/schedule/staff/html/
Authorization: Bearer {access_token}
```

**Response:** Complete HTML document with embedded CSS styling

**Content-Type:** `text/html`

**Android Implementation (Kotlin - Using WebView directly):**
```kotlin
// Using OkHttpClient with interceptor for authentication
val okHttpClient = OkHttpClient.Builder()
    .addInterceptor { chain ->
        val request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer $accessToken")
            .build()
        chain.proceed(request)
    }
    .build()

val webView = findViewById<WebView>(R.id.scheduleWebView)
webView.webViewClient = object : WebViewClient() {
    override fun onPageFinished(view: WebView?, url: String?) {
        super.onPageFinished(view, url)
        // Page loaded successfully with CSS
    }
}

// Load the API endpoint directly
webView.loadUrl(
    "http://10.0.2.2:8000/api/schedule/staff/html/",
    mapOf("Authorization" to "Bearer $accessToken")
)
```

**Android Implementation (Kotlin - Fetching and displaying):**
```kotlin
val client = OkHttpClient()
val request = Request.Builder()
    .url("http://10.0.2.2:8000/api/schedule/staff/html/")
    .addHeader("Authorization", "Bearer $accessToken")
    .build()

client.newCall(request).enqueue(object : Callback {
    override fun onFailure(call: Call, e: IOException) {
        e.printStackTrace()
    }

    override fun onResponse(call: Call, response: Response) {
        if (response.isSuccessful) {
            val htmlContent = response.body?.string() ?: ""
            runOnUiThread {
                webView.loadDataWithBaseURL(
                    null,
                    htmlContent,
                    "text/html",
                    "UTF-8",
                    null
                )
            }
        }
    }
})
```

---

### 2. **Get Faculty Schedule as HTML** (Admin View)
```
GET /api/schedule/faculty/html/
Authorization: Bearer {access_token}
```

Same as staff schedule - returns complete HTML with CSS styling.

**This endpoint is identical to staff schedule HTML endpoint.**

---

### 3. **Download Staff Schedule as HTML** (For PDF/Printing)
```
GET /api/schedule/staff/pdf/
Authorization: Bearer {access_token}
```

**Response:** Complete HTML document with embedded CSS (same as HTML endpoint)

**Used for:** Android's native Print Manager to generate PDF

**Android Implementation (Kotlin):**
```kotlin
fun downloadAndPrintSchedule() {
    val request = Request.Builder()
        .url("http://10.0.2.2:8000/api/schedule/staff/pdf/")
        .addHeader("Authorization", "Bearer $accessToken")
        .build()
    
    client.newCall(request).enqueue(object : Callback {
        override fun onFailure(call: Call, e: IOException) {
            // Handle error
        }
        
        override fun onResponse(call: Call, response: Response) {
            if (response.isSuccessful) {
                val htmlContent = response.body?.string() ?: ""
                runOnUiThread {
                    webView.loadDataWithBaseURL(null, htmlContent, "text/html", "UTF-8", null)
                    // Now use Print Manager
                    val printManager = getSystemService(Context.PRINT_SERVICE) as PrintManager
                    val printAdapter = webView.createPrintDocumentAdapter("Schedule")
                    printManager.print("Print Schedule", printAdapter, PrintAttributes.Builder().build())
                }
            }
        }
    })
}
```

---

### 4. **Download Faculty Schedule as HTML** (For PDF/Printing)
```
GET /api/schedule/faculty/pdf/
Authorization: Bearer {access_token}
```

Same as staff PDF endpoint - returns HTML that can be printed to PDF.

---

### Complete Android Integration Example

### Step 1: Setup OkHttpClient with Authentication
```kotlin
object RetrofitClient {
    private const val BASE_URL = "http://10.0.2.2:8000/"
    
    fun getClient(accessToken: String): OkHttpClient {
        return OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request().newBuilder()
                    .addHeader("Authorization", "Bearer $accessToken")
                    .build()
                chain.proceed(request)
            }
            .build()
    }
}
```

### Step 2: Create Schedule Base Activity
```kotlin
abstract class ScheduleBaseActivity : AppCompatActivity() {
    protected lateinit var webView: WebView
    protected var accessToken: String = ""
    protected val client by lazy { RetrofitClient.getClient(accessToken) }
    
    protected fun loadScheduleIntoWebView(endpoint: String) {
        val request = Request.Builder()
            .url("http://10.0.2.2:8000$endpoint")
            .addHeader("Authorization", "Bearer $accessToken")
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    Toast.makeText(this@ScheduleBaseActivity, 
                        "Error loading schedule: ${e.message}", 
                        Toast.LENGTH_SHORT).show()
                }
            }
            
            override fun onResponse(call: Call, response: Response) {
                if (response.isSuccessful) {
                    val htmlContent = response.body?.string() ?: ""
                    runOnUiThread {
                        webView.loadDataWithBaseURL(
                            null,
                            htmlContent,
                            "text/html",
                            "UTF-8",
                            null
                        )
                    }
                } else {
                    runOnUiThread {
                        Toast.makeText(this@ScheduleBaseActivity,
                            "Error: ${response.code}",
                            Toast.LENGTH_SHORT).show()
                    }
                }
            }
        })
    }
}
```

### Step 3: Display Staff Schedule in Activity
```kotlin
class StaffScheduleActivity : ScheduleBaseActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_schedule)
        
        webView = findViewById(R.id.scheduleWebView)
        accessToken = intent.getStringExtra("access_token") ?: ""
        
        configureWebView()
        loadScheduleIntoWebView("/api/schedule/staff/html/")
    }
    
    private fun configureWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            setSupportZoom(true)
            builtInZoomControls = true
            displayZoomControls = false
            useWideViewPort = true
            loadWithOverviewMode = true
        }
        
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                // CSS and styling should now be applied
            }
        }
    }
    
    fun printSchedule() {
        val printManager = getSystemService(Context.PRINT_SERVICE) as PrintManager
        val printAdapter = webView.createPrintDocumentAdapter("Staff_Schedule")
        printManager.print("Print Schedule", printAdapter, PrintAttributes.Builder().build())
    }
}
```

### Step 4: Display Faculty Schedule in Activity
```kotlin
class FacultyScheduleActivity : ScheduleBaseActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_schedule)
        
        webView = findViewById(R.id.scheduleWebView)
        accessToken = intent.getStringExtra("access_token") ?: ""
        
        configureWebView()
        loadScheduleIntoWebView("/api/schedule/faculty/html/")
    }
    
    private fun configureWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            setSupportZoom(true)
            builtInZoomControls = true
            displayZoomControls = false
        }
    }
}
```

---

## Authentication

All schedule endpoints require JWT token authentication using Bearer tokens (not session-based auth):

### Step 1: Get JWT Token
```
POST /api/auth/token/
Content-Type: application/json

{
  "username": "faculty_username",
  "password": "faculty_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Step 2: Use Bearer Token in Authorization Header
```
GET /api/schedule/staff/html/
Authorization: Bearer {access_token}
```

**Important:** 
- Use `Authorization: Bearer <token>` NOT `Authorization: Token <token>`
- The schedule API endpoints use DRF's `IsAuthenticated` permission class
- They do NOT use session-based authentication (Django `@login_required`)
- Session-based auth would redirect to login page - Bearer tokens bypass this

### Step 3: Refresh Token When Expired (Optional)
```
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "refresh_token"
}
```

**Response:**
```json
{
  "access": "new_access_token_here",
  "refresh": "refresh_token"
}
```

---

## How It Works

**Old Approach (❌ Complex):**
- API returned JSON with HTML embedded inside
- Android parsed JSON, extracted HTML, loaded in WebView
- CSS sometimes failed to load properly in WebView

**New Approach (✅ Simple):**
- API returns HTML directly with full CSS
- Content-Type: `text/html`
- Android loads it directly in WebView with all styles applied
- Much better rendering and faster loading

---

## Troubleshooting

### Issue: Getting Redirected to Login Page
**Symptom:** Print preview shows "Login" HTML instead of schedule
**Cause:** Missing or incorrect Authorization header
**Solution:** 
- Make sure you're sending: `Authorization: Bearer {your_access_token}`
- Do NOT send `Token` prefix, use `Bearer` only
- Token must be from `/api/auth/token/` endpoint
- Check that token is not expired

Example in Android (Kotlin):
```kotlin
val request = Request.Builder()
    .url("http://10.0.2.2:8000/api/schedule/staff/html/")
    .addHeader("Authorization", "Bearer $accessToken")  // <- Correct format
    .build()
```

### Issue: 404 Not Found
- Make sure you're using the correct endpoint URL
- Verify JWT token is valid and not expired
- Ensure server is running (test with browser: http://localhost:8000/)

### Issue: 403 Forbidden
**Cause:** Token is valid but user is not authenticated
**Solution:**
- Get a new token using `/api/auth/token/`
- Verify username/password are correct
- If token expired, use refresh token to get new access token

### Issue: CORS Error
- The backend allows authenticated requests
- Ensure your Authorization header is correct
- Check that Content-Type is application/json when needed

### Issue: WebView Shows Blank
- Check browser console (use Chrome DevTools remote debugging)
- Verify JavaScript is enabled in WebView settings
- Check network tab to see if HTML was downloaded
- Look for 401/403 errors in network requests

### Issue: PDF Won't Download
- Use Android's Print Manager with `webView.createPrintDocumentAdapter()`
- For direct download, handle the ResponseBody from the PDF endpoint
- Ensure file permissions are granted (READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE)

---

## Server Configuration

Your server is running at:
- **Base URL:** `http://your-server-ip:port/`
- **Example:** `http://192.168.1.100:8000/`

Update the `BASE_URL` in your Android app accordingly.

---

## Next Steps

1. Implement the API service in your Android project
2. Create UI to display schedules
3. Add print/PDF export functionality
4. Test on actual Android device
5. Deploy server to production (Render, Railway, or your choice)

For questions or issues, check the Django views in `hello/views.py` for the backend implementation.
