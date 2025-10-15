package com.pythonnative.android_template

import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.util.Log
import android.widget.TextView
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // setContentView(R.layout.activity_main)

        // Initialize Chaquopy
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        try {
            val py = Python.getInstance()
            val pyModule = py.getModule("app.main_page")
            pyModule.callAttr("bootstrap", this)
            // Python Page will set the content view via set_root_view
        } catch (e: Exception) {
            Log.e("PythonNative", "Python bootstrap failed", e)
            // Fallback: show a simple native label if Python bootstrap fails
            val tv = TextView(this)
            tv.text = "Hello from PythonNative (Android template)"
            setContentView(tv)
        }
    }
}