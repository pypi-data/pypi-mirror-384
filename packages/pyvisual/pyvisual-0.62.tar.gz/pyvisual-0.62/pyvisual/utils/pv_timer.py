from PySide6.QtCore import QTimer

class PvTimer:
    """
    A wrapper class for QTimer that provides a simplified interface 
    for timer-based functionality in PyVisual.
    """
    
    def __init__(self, interval=100, callback=None, single_shot=False):
        """
        Initialize a new timer.
        
        Args:
            interval: Timer interval in milliseconds
            callback: Function to call when the timer times out
            single_shot: If True, the timer will only fire once
        """
        self._timer = QTimer()
        self._interval = interval
        self._callback = callback
        self._single_shot = single_shot
        
        # Configure the timer
        if callback:
            self._timer.timeout.connect(callback)
        
        if single_shot:
            self._timer.setSingleShot(True)
    
    def start(self):
        """Start the timer with the current interval."""
        self._timer.start(self._interval)
        
    def stop(self):
        """Stop the timer."""
        self._timer.stop()
        
    def is_active(self):
        """Return whether the timer is running."""
        return self._timer.isActive()
    
    @property
    def interval(self):
        """Get the current timer interval in milliseconds."""
        return self._interval
    
    @interval.setter
    def interval(self, value):
        """Set the timer interval in milliseconds."""
        self._interval = value
        # Restart the timer if it's active
        if self.is_active():
            self.stop()
            self.start()
    
    @property
    def callback(self):
        """Get the current callback function."""
        return self._callback
    
    @callback.setter
    def callback(self, func):
        """Set the callback function to be called when the timer times out."""
        # Disconnect the old callback if there is one
        if self._callback:
            try:
                self._timer.timeout.disconnect(self._callback)
            except:
                pass
                
        # Set and connect the new callback
        self._callback = func
        if func:
            self._timer.timeout.connect(func)
    
    @property
    def single_shot(self):
        """Get whether the timer is single-shot."""
        return self._single_shot
    
    @single_shot.setter
    def single_shot(self, value):
        """Set whether the timer is single-shot."""
        self._single_shot = value
        self._timer.setSingleShot(value) 