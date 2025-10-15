#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Progress indicators and visual effects for SpeedTest
"""

import sys
import time
import threading
from typing import Optional, Callable


class ProgressIndicator:
    """Base class for progress indicators"""
    
    def __init__(self):
        self.is_running = False
        self._thread = None
        
    def start(self):
        self.is_running = True
        
    def stop(self):
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join()
            
    def update(self, value: float, message: str = ""):
        pass


class SpinnerProgress(ProgressIndicator):
    """Spinning progress indicator"""
    
    SPINNERS = {
        'dots': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
        'line': ['|', '/', '-', '\\'],
        'arrows': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
        'clock': ['🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛'],
        'moon': ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']
    }
    
    def __init__(self, style: str = 'dots', message: str = "Loading"):
        super().__init__()
        self.style = style
        self.message = message
        self.frames = self.SPINNERS.get(style, self.SPINNERS['dots'])
        self.current_frame = 0
        
    def start(self):
        super().start()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        
    def _animate(self):
        while self.is_running:
            frame = self.frames[self.current_frame % len(self.frames)]
            sys.stdout.write(f'\r{frame} {self.message}')
            sys.stdout.flush()
            self.current_frame += 1
            time.sleep(0.1)
    
    def stop(self, final_message: str = ""):
        super().stop()
        # Clear the spinner line completely
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        if final_message:
            sys.stdout.write(f'{final_message}\n')
        sys.stdout.flush()


class ProgressBar(ProgressIndicator):
    """Progress bar indicator"""
    
    def __init__(self, width: int = 40, fill_char: str = '█', empty_char: str = '░'):
        super().__init__()
        self.width = width
        self.fill_char = fill_char
        self.empty_char = empty_char
        
    def update(self, progress: float, message: str = ""):
        if not 0 <= progress <= 1:
            progress = max(0, min(1, progress))
            
        filled = int(progress * self.width)
        bar = self.fill_char * filled + self.empty_char * (self.width - filled)
        percentage = int(progress * 100)
        
        sys.stdout.write(f'\r[{bar}] {percentage}% {message}')
        sys.stdout.flush()
        
    def finish(self, message: str = ""):
        # Clear the progress bar line completely
        clear_width = self.width + 40  # Extra space for percentage and message
        sys.stdout.write('\r' + ' ' * clear_width + '\r')
        if message:
            sys.stdout.write(f'{message}\n')
        else:
            print()  # Just new line
        sys.stdout.flush()


class AnimatedProgress(ProgressIndicator):
    """Animated progress with custom effects"""
    
    def __init__(self, style: str = 'wave'):
        super().__init__()
        self.style = style
        self.position = 0
        
    def start(self):
        super().start()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        
    def _animate(self):
        while self.is_running:
            if self.style == 'wave':
                wave = '～～～～～～～～～～'
                display = wave[self.position:] + wave[:self.position]
                sys.stdout.write(f'\r🌊 {display[:10]}')
            elif self.style == 'bouncing':
                dots = '●○○○○○○○○○'
                display = dots[self.position:] + dots[:self.position]
                sys.stdout.write(f'\r⚡ {display[:10]}')
            elif self.style == 'pulse':
                pulse_chars = ['💙', '💚', '💛', '🧡', '❤️', '💜']
                char = pulse_chars[self.position % len(pulse_chars)]
                sys.stdout.write(f'\r{char} Testing... {char}')
                
            sys.stdout.flush()
            self.position = (self.position + 1) % 10
            time.sleep(0.2)
            
    def stop(self, final_message: str = ""):
        super().stop()
        # Clear the animation line completely
        sys.stdout.write('\r' + ' ' * 30 + '\r')
        if final_message:
            sys.stdout.write(f'{final_message}\n')
        sys.stdout.flush()


class MultiStageProgress:
    """Multi-stage progress indicator"""
    
    def __init__(self, stages: list):
        self.stages = stages
        self.current_stage = 0
        self.stage_progress = 0.0
        
    def next_stage(self):
        if self.current_stage < len(self.stages) - 1:
            self.current_stage += 1
            self.stage_progress = 0.0
            
    def update_stage_progress(self, progress: float):
        self.stage_progress = max(0, min(1, progress))
        
    def get_overall_progress(self) -> float:
        if not self.stages:
            return 1.0
            
        stage_weight = 1.0 / len(self.stages)
        overall = self.current_stage * stage_weight
        overall += self.stage_progress * stage_weight
        return overall
        
    def display(self):
        if self.current_stage < len(self.stages):
            stage_name = self.stages[self.current_stage]
            overall_percent = int(self.get_overall_progress() * 100)
            stage_percent = int(self.stage_progress * 100)
            
            # Create mini progress bar
            bar_width = 20
            filled = int(self.stage_progress * bar_width)
            bar = '█' * filled + '░' * (bar_width - filled)
            
            sys.stdout.write(f'\r[{bar}] {stage_name} ({stage_percent}%) | Overall: {overall_percent}%')
            sys.stdout.flush()
            
    def finish(self, final_message: str = ""):
        # Clear current progress line
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        if final_message:
            sys.stdout.write(f'{final_message}\n')
        else:
            print()  # Just new line
        sys.stdout.flush()


class SpeedTestProgress:
    """Specialized progress for speed tests"""
    
    def __init__(self):
        self.start_time = None
        self.bytes_transferred = 0
        
    def start_test(self, test_name: str):
        self.start_time = time.time()
        self.bytes_transferred = 0
        print(f"\n🚀 Starting {test_name} test...")
        
    def update_speed(self, speed_mbps: float, bytes_transferred: int):
        self.bytes_transferred = bytes_transferred
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        # Format speed
        if speed_mbps >= 1000:
            speed_str = f"{speed_mbps/1000:.2f} Gbps"
        elif speed_mbps >= 1:
            speed_str = f"{speed_mbps:.2f} Mbps"
        else:
            speed_str = f"{speed_mbps*1000:.0f} Kbps"
            
        # Format bytes
        if bytes_transferred >= 1024**3:  # GB
            bytes_str = f"{bytes_transferred/(1024**3):.2f} GB"
        elif bytes_transferred >= 1024**2:  # MB
            bytes_str = f"{bytes_transferred/(1024**2):.2f} MB"
        elif bytes_transferred >= 1024:  # KB
            bytes_str = f"{bytes_transferred/1024:.2f} KB"
        else:
            bytes_str = f"{bytes_transferred} B"
            
        # Speed indicator animation
        indicators = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        level = min(len(indicators) - 1, int(speed_mbps / 10))
        indicator = indicators[level]
        
        sys.stdout.write(f'\r{indicator} Speed: {speed_str} | Data: {bytes_str} | Time: {elapsed:.1f}s')
        sys.stdout.flush()
        
    def finish_test(self, final_speed: float, test_type: str = "Test"):
        # Clear the speed line completely
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()
        # Don't print here - let caller handle the final message


# Utility functions for easy usage
def show_spinner(message: str = "Loading", style: str = 'dots') -> SpinnerProgress:
    """Create and start a spinner"""
    spinner = SpinnerProgress(style=style, message=message)
    spinner.start()
    return spinner


def show_progress_bar(width: int = 40) -> ProgressBar:
    """Create a progress bar"""
    return ProgressBar(width=width)


def show_animated_progress(style: str = 'wave') -> AnimatedProgress:
    """Create and start animated progress"""
    progress = AnimatedProgress(style=style)
    progress.start()
    return progress


def create_multi_stage(stages: list) -> MultiStageProgress:
    """Create multi-stage progress"""
    return MultiStageProgress(stages)


def create_speed_progress() -> SpeedTestProgress:
    """Create speed test progress"""
    return SpeedTestProgress()