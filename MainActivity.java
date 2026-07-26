package com.musicheal.app;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        final Button btnHeal = findViewById(R.id.btnHeal);
        final TextView txtConsole = findViewById(R.id.txtConsole);

        btnHeal.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                txtConsole.setText("Invoking MusicHeal System...\n");
                try {
                    Python py = Python.getInstance();
                    PyObject pyModule = py.getModule("main");
                    String consoleData = pyModule.callAttr("run_engine").toString();
                    txtConsole.append(consoleData);
                } catch (Exception e) {
                    txtConsole.append("\nExecution Failure: " + e.getMessage());
                }
            }
        });
    }
}
