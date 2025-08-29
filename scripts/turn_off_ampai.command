#!/bin/bash
# Turn Off Liam System (LLM + Web Server)
# Double-click this file to stop both servers

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "🎨 ╔══════════════════════════════════════════════════════════════╗"
echo "🎨 ║                        Liam System                           ║"
echo "🎨 ║                    🛑 Shutting Down...                       ║"
echo "🎨 ╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check what's running
LLM_RUNNING=false
WEB_RUNNING=false

echo "🔍 Checking system status..."
echo ""

# Check LLM server
if check_port 8000; then
            if pgrep -f "llama-server.*8000" >/dev/null; then
            echo "✅ LLM server running on port 8000"
            LLM_RUNNING=true
        else
            echo "⚠️  Port 8000 in use by another service"
        fi
else
    echo "ℹ️  No LLM server on port 8000"
fi

# Check web server
if check_port 8081; then
    if pgrep -f "web_chat.py" >/dev/null; then
        echo "✅ Web server running on port 8081"
        WEB_RUNNING=true
    else
        echo "⚠️  Port 8081 in use by another service"
    fi
else
    echo "ℹ️  No web server on port 8081"
fi

echo ""

if [ "$LLM_RUNNING" = false ] && [ "$WEB_RUNNING" = false ]; then
    echo "ℹ️  No Liam services are currently running"
    echo ""
    read -p "Press Enter to close this window..."
    exit 0
fi

echo "🛑 Stopping Liam services..."

# Stop LLM server
if [ "$LLM_RUNNING" = true ]; then
    echo "🤖 Stopping LLM server..."
    pkill -f "llama-server.*8000"
    sleep 3
    
    # Check if it's still running
    if check_port 8000; then
        echo "⚠️  Graceful shutdown failed, forcing stop..."
        pkill -9 -f "llama-server.*8000"
        sleep 2
    fi
    
    # Final check
    if check_port 8000; then
        echo "❌ Failed to stop LLM server"
    else
        echo "✅ LLM server stopped"
    fi
fi

# Stop web server
if [ "$WEB_RUNNING" = true ]; then
    echo "🌐 Stopping web server..."
    pkill -f "web_chat.py"
    sleep 2
    
    # Check if it's still running
    if check_port 8081; then
        echo "⚠️  Graceful shutdown failed, forcing stop..."
        pkill -9 -f "web_chat.py"
        sleep 2
    fi
    
    # Final check
    if check_port 8081; then
        echo "❌ Failed to stop web server"
    else
        echo "✅ Web server stopped"
    fi
fi

echo ""
echo "🎯 Final status check..."

# Final verification
if check_port 8000; then
    echo "⚠️  Port 8000 still in use"
else
    echo "✅ Port 8000 is free"
fi

if check_port 8081; then
    echo "⚠️  Port 8081 still in use"
else
    echo "✅ Port 8081 is free"
fi

echo ""
echo "✅ Liam System stopped successfully!"

# Try to close the Liam browser tab
echo "🌐 Attempting to close Liam browser tab..."
if command -v osascript >/dev/null 2>&1; then
    # Close Liam tab in Safari/Chrome
    osascript -e '
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
        end tell
        
        if frontApp is "Safari" then
            tell application "Safari"
                repeat with w in windows
                    repeat with t in tabs of w
                        if URL of t contains "localhost:8081" then
                            close t
                            return "Safari tab closed"
                        end if
                    end repeat
                end repeat
            end tell
        else if frontApp is "Google Chrome" then
            tell application "Google Chrome"
                repeat with w in windows
                    repeat with t in tabs of w
                    if URL of t contains "localhost:8081" then
                        close t
                        return "Chrome tab closed"
                    end if
                end repeat
            end tell
        end if
    ' 2>/dev/null && echo "✅ Browser tab closed" || echo "ℹ️  No Liam tab found to close"
else
    echo "ℹ️  AppleScript not available, tab will remain open"
fi

echo ""
echo "💡 To start the system again, use: start_llm.command"
echo ""
read -p "Press Enter to close this window..."
